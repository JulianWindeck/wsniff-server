from flask import request, jsonify, current_app as app, Blueprint, g
from sqlalchemy import exc
from marshmallow import ValidationError

from server import db
from server.models import AccessPoint, WardrivingMap, Sniffer
from server.endpoints.api_definition import map_schema, maps_schema, sniffers_schema
from server.login import login_required

maps = Blueprint('maps', __name__, url_prefix='/maps')


###############################################ROUTES########################################

"""
Get all maps
"""
@maps.route('', methods=['GET'])
@login_required
def get_all_maps():
    maps = WardrivingMap.query.all()

    output = maps_schema.dump(maps)
    return jsonify({'maps': output})

"""
Retrieve the information of a single map
"""
@maps.route('/<id>', methods=['GET'])
@login_required
def get_map(id):
    ap = WardrivingMap.query.filter_by(id=id).first_or_404()

    return jsonify({'map': map_schema.dump(ap)}) 

"""
Create a new map
"""
@maps.route('', methods=['POST'])
@login_required
def create_map():
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


"""
Update map information
"""
@maps.route('/<id>', methods=['PUT'])
@login_required
def update_map(id):
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


"""
Add a list of Access Points to map <id>
Expects a list of <mac>-IDs which belong to the APs as JSON input.
"""
@maps.route('/<id>/aps', methods=['POST'])
@login_required
def add_ap(id):
    map = WardrivingMap.query.filter_by(id=id).first_or_404()

    input = request.get_json()
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


"""
Get all contributing sniffers of this map
"""
@maps.route('/<id>/sniffers', methods=['GET'])
@login_required
def get_all_sniffers(id):
   map = WardrivingMap.query.filter_by(id=id).first_or_404() 
   return jsonify({'sniffers': sniffers_schema.dump(map.sniffers)})

"""
Add the current sniffer as a contributer to this map
"""
@maps.route('/<id>/sniffers', methods=['POST'])
@login_required
def add_sniffer(id):
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