from flask import request, jsonify, current_app as app, Blueprint, g
from sqlalchemy import exc
from marshmallow import ValidationError

from server import db
from server.models import AccessPoint, WardrivingMap, Sniffer, Discovery, Map_StringEAV
from server.endpoints.api_definition import map_schema, maps_schema, sniffers_schema, discovery_schema, discoveries_schema
from server.login import login_required

maps = Blueprint('maps', __name__, url_prefix='/maps')


###############################################ROUTES########################################


@maps.route('', methods=['GET'])
@login_required
def get_all_maps():
    """
    Get all maps including their generic eav attributes
    """
    maps = WardrivingMap.query.all()

    output = maps_schema.dump(maps)
    return jsonify({'maps': output})


@maps.route('/<id>', methods=['GET'])
@login_required
def get_map(id):
    """
    Retrieve the information of a single map (including the generic eav attributes)
    """
    ap = WardrivingMap.query.filter_by(id=id).first_or_404()

    return jsonify({'map': map_schema.dump(ap)}) 


@maps.route('', methods=['POST'])
@login_required
def create_map():
    """
    Create a new map
    """
    try: 
        map = map_schema.load(request.get_json())
    except ValidationError as e:
        return jsonify(e.messages), 400

    try:
        db.session.add(map)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured.'}), 400

    return jsonify({'message': 'New map created.', 'map_id': map.id})



@maps.route('/<id>', methods=['PUT'])
@login_required
def update_map(id):
    """
    Update map information
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404()

    try:
        #update existing object 
        map = map_schema.load(request.get_json(), instance=map)
    except ValidationError as e:
       return jsonify(e.messages), 400 

    try:
        db.session.add(map)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured.'}), 400

    return jsonify({'message': 'Map has been updated.'})

@maps.route('/<id>/meta', methods=["POST"])
@login_required
def add_map_metadata(id):
    """
    Dynamically add map attributes
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404()
    
    #get post data
    input = request.get_json(silent=True)
    if not input:
        return jsonify({'message': 'You have to provide an attribute and a value.'}), 400
    attribute = input.get('attribute')
    value = input.get('value')
    if not (attribute and value):
        return jsonify({'message': 'You have to provide an attribute and a value.'}), 400

    #add attribute to map
    eav = Map_StringEAV(map_id=id, attribute=attribute, value=value)
    try:
        db.session.add(eav)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'DB integrity error occured.'}), 400

    return jsonify({'message': f'Attribute <{attribute}> added to map {id}.'}), 200


@maps.route('/<id>', methods=['POST'])
@login_required
def add_discovery(id):
    """
    Create a new discovery and add it to the map.
    If there is no corresponding Access Point for this discovery, 
    a new AP is also created in the process.
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404()

    #load Discovery object from JSON input
    try:
        discovery = discovery_schema.load(request.get_json())
    except ValidationError as e:
        return jsonify(e.messages), 400

    #if this is the first time the AP is discovered, add the AP
    #check whether there already is an AP with this mac
    ap = AccessPoint.query.filter_by(mac=discovery.access_point_mac).first()

    if ap:
        #if there is, add this discovery to the ap
        #and update the values of the AP
        ap.update(discovery)
    
    #if this is the first time the AP is discovered
    else:
        #also automatically sets this AP as the access_point of the current discovery
        ap = AccessPoint(mac=discovery.access_point_mac)
        ap.update(discovery)

        try:
            db.session.add(ap)
            db.session.commit()
        except exc.IntegrityError as e:
            return jsonify({'message': 'Integrity error occured when adding AP.'}), 400
    
    #as foreign key we can use the current user object
    discovery.sniffer_id = g.current_user.id
    #add discovery to map
    discovery.map_id = map.id

    try:
        db.session.add(discovery)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured when adding discovery.'}), 400

    return jsonify({'message': 'New discovery was added.'})


@maps.route('/<id>/aps', methods=['GET'])
#@login_required
def get_aps(id):
    """
    Returns all discoveries that belong to this map that are within the rectangle defined by 
    [lat1, lon1] and [lat2, lon2]
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404()

    #get query parameters
    lat1, lat2 = request.args.get('lat1'), request.args.get('lat2')
    lon1, lon2 = request.args.get('lon1'), request.args.get('lon2')

    if not (lat1 and lat2 and lon1 and lon2):
        return jsonify({'message': 'Please provide lat and lon values'}), 400

    lat_min, lon_min = min(lat1, lat2), min(lon1, lon2)
    lat_max, lon_max = max(lat1, lat2), max(lon1, lon2)

    #NOTE: (idea) add a route in the future that only displays unique APs
    # AccessPoint.query.join(AccessPoint.maps).filter(WardrivingMap.id == id) \
    #     .filter(AccessPoint.lat <= lat_max, AccessPoint.lat >= lat_min,
    #             AccessPoint.lon <= lon_max, AccessPoint.lon >= lon_min).all()
    discoveries = Discovery.query.filter_by(map_id=map.id).filter( 
        Discovery.gps_lat >= lat_min, Discovery.gps_lat <= lat_max, 
        Discovery.gps_lon >= lon_min, Discovery.gps_lon <= lon_max).all()

    return jsonify({'discoveries': discoveries_schema.dump(discoveries)})



@maps.route('/<id>/sniffers', methods=['GET'])
@login_required
def get_all_sniffers(id):
    """
    Get all contributing sniffers of this map
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404() 
    return jsonify({'sniffers': sniffers_schema.dump(map.sniffers)})


@maps.route('/<id>/sniffers', methods=['POST'])
@login_required
def add_sniffer(id):
    """
    Add the current sniffer as a contributer to this map
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404()

    print(g.current_user.id)
    sniffer = Sniffer.query.filter_by(id=g.current_user.id).first()
    if not sniffer:
        return jsonify({'message': 'Sniffer with this id could not be found. Maybe you are \
                                    trying to add the admin user as a Sniffer to this map.'})          
    map.sniffers.append(sniffer)

    try:
        db.session.add(map)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured.'}), 400

    return jsonify({'message': 'Added sniffer as contributer to map.'}), 200