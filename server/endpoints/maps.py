from flask import request, jsonify, current_app as app, Blueprint, g
from sqlalchemy import exc
from marshmallow import ValidationError

from server import db
from server.models import AccessPoint, WardrivingMap, Sniffer, Map_StringEAV
from server.endpoints.api_definition import map_schema, maps_schema, sniffers_schema
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

    return jsonify({'message': 'New map created.'})



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


@maps.route('/<id>/aps', methods=['POST'])
@login_required
def add_ap(id):
    """
    Add a list of Access Points to map <id>
    Expects a list of <mac>-IDs which belong to the APs as JSON input.
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404()

    input = request.get_json(silent=True)
    if not input or not input.get('aps'):
        return jsonify({'message': 'You have to input a list of MACs that identify the APs you want to add.'}), 400
    
    print(input['aps'])
    aps = AccessPoint.query.filter(AccessPoint.mac.in_(input['aps'])).all()
    map.access_points.extend(aps)

    try:
        db.session.add(map)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured.'}), 400

    return jsonify({'message': 'Added access points to map.'}), 200


@maps.route('/<id>/aps', methods=['GET'])
@login_required
def get_aps(id):
    """
    Returns all APs that belong to this map that are within the rectangle defined by 
    [lat1, lon1] and [lat2, lon2]
    """
    map = WardrivingMap.query.filter_by(id=id).first_or_404()

    #get query parameters
    lat1, lat2 = request.args.get('lat1'), request.args.get('lat2')
    lon1, lon2 = request.args.get('lon1'), request.args.get('lon2')

    if not (lat1 and lat2 and lon1 and lon2):
        return jsonify({'message', 'Please provide lat and lon values'}), 400

    lat_min, lon_min = min(lat1, lat2), min(lon1, lon2)
    lat_max, lon_max = max(lat1, lat2), max(lon1, lon2)

    AccessPoint.query.join(AccessPoint.maps).filter(WardrivingMap.id == id) \
        .filter(AccessPoint.lat <= lat_max, AccessPoint.lat >= lat_min,
                AccessPoint.lon <= lon_max, AccessPoint.lon >= lon_min).all()
    return



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