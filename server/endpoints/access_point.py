from flask import request, jsonify, current_app as app, Blueprint, g
from sqlalchemy import exc
from marshmallow import ValidationError

from server import db, ma
from server.models import AccessPoint, Discovery
from server.login import admin_required, login_required
from server.endpoints.api_definition import discovery_schema, discoveries_schema, ap_schema, aps_schema

aps = Blueprint('aps', __name__, url_prefix='/aps')


###############################################AccessPoints#######################################
"""
Get all Access Points (without their discoveries)
"""
@aps.route('', methods=['GET'])
@login_required
def get_all_aps():
    aps = AccessPoint.query.all()

    output = aps_schema.dump(aps)
    return jsonify({'aps': output})

"""
Create a new Access Point
"""
@aps.route('', methods=['POST'])
@login_required
def create_ap():
    try: 
        ap = ap_schema.load(request.get_json())
    except ValidationError as e:
        return jsonify(e.messages), 400

    try:
        db.session.add(ap)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured.'}), 400

    return jsonify({'message': 'New access point created.'})

"""
Retrieve the information of a single AP,
INCLUDING all discoveries linked to that AP
"""
@aps.route('/<mac>', methods=['GET'])
@login_required
def get_ap(mac):
    ap = AccessPoint.query.filter_by(mac=mac).first_or_404()

    return jsonify({'ap': ap_schema.dump(ap)})              


"""Update access point"""
@aps.route('/<mac>', methods=['PUT'])
@login_required
def update_ap(mac):
    ap = AccessPoint.query.filter_by(mac=mac).first_or_404()

    try:
        #update existing object 
        ap = ap_schema.load(request.get_json(), instance=ap)
    except ValidationError as e:
       return jsonify(e.messages), 400 

    db.session.add(ap)
    db.session.commit()

    return jsonify({'message': 'AP has been updated.'})

@aps.route('/<mac>', methods=['DELETE'])
@login_required
def delete_ap(mac):
    ap = AccessPoint.query.filter_by(mac=mac).first_or_404()

    db.session.delete(ap)
    db.session.commit()

    return jsonify({'message': 'AP has been deleted.'})

#################################################DISCOVERIES######################################


"""
Add a discovery for the Access Point with MAC address <mac> 
If there is no corresponding Access Point for this discovery, a new AP is also created in the process.
"""
@aps.route('/<mac>', methods=['POST'])
@login_required
def add_discovery(mac:str):
    #check whether there is an AP with this mac
    ap = AccessPoint.query.filter_by(mac=mac).first()
    if not ap:
        return jsonify({'message': 'You have to add a corresponding AP first.'}), 404

    #load Discovery object from JSON input
    try:
        discovery = discovery_schema.load(request.get_json())
    except ValidationError as e:
        return jsonify(e.messages), 400

    if str(discovery.access_point_mac) != mac:
        return jsonify({'message': 'MAC of URL and input data do not match.',
                        'vergleich':f"{mac} <-> {discovery.access_point_mac}"})
    
    #as foreign key we can use the current user object
    discovery.sniffer_id = g.current_user.id

    try:
        db.session.add(discovery)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured.'}), 400

    return jsonify({'message': 'New discovery was added.'})

@aps.route('/<mac>/<discovery_id>', methods=['DELETE'])
@login_required
def delete_discovery(mac, discovery_id):
    dis = Discovery.query.filter_by(id=discovery_id).first_or_404()

    db.session.delete(dis)
    db.session.commit()

    return jsonify({'message': 'Discovery has been deleted.'})

"""
Show all discoveries. Primarily intended for debugging.
"""
@aps.route('/*', methods=['GET'])
@login_required
def get_all_discoveries():
    discoveries = Discovery.query.all()
    return jsonify({'discoveries': discoveries_schema.dump(discoveries)})