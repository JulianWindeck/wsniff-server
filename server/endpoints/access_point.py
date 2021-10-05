from flask import request, jsonify, current_app as app, Blueprint, g
from sqlalchemy import exc
from marshmallow import ValidationError

from server import db, ma
from server.models import AccessPoint, Discovery, AP_EAV
from server.login import admin_required, login_required
from server.endpoints.api_definition import discovery_schema, discoveries_schema, ap_schema, aps_schema

aps = Blueprint('aps', __name__, url_prefix='/aps')


###############################################AccessPoints#######################################

@aps.route('', methods=['GET'])
@login_required
def get_all_aps():
    """
    Get all Access Points (without their discoveries)
    """
    aps = AccessPoint.query.all()

    output = aps_schema.dump(aps)
    return jsonify({'aps': output})

@aps.route('/<mac>', methods=["POST"])
@login_required
def add_ap_attribute(mac):
    """
    Dynamically add access point attributes
    """
    ap = AccessPoint.query.filter_by(mac=mac).first_or_404()
    
    #get and validate post data
    input = request.get_json(silent=True)
    if not input:
        return jsonify({'message': 'You have to provide an attribute, a value and a type.'}), 400
    attribute = input.get('attribute')
    value = input.get('value')
    type = input.get('type')
    if not (attribute and value and type):
        return jsonify({'message': 'You have to provide an attribute, a value and a type.'}), 400
    if not (type=="String" or type=="Integer" or type=="Real"):
        return jsonify({'message': 'Attribute type has to be either "String" or "Integer" or "Real".'}), 400

    #add attribute to map
    eav = AP_EAV(mac=mac, attribute=attribute, value=value, type=type)
    try:
        db.session.add(eav)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'DB integrity error occured.'}), 400

    return jsonify({'message': f'Attribute <{attribute}> added to AP {mac}.'}), 200


@aps.route('/<mac>', methods=['GET'])
@login_required
def get_ap(mac):
    """
    Retrieve the information of a single AP,
    INCLUDING all discoveries linked to that AP
    """
    ap = AccessPoint.query.filter_by(mac=mac).first_or_404()

    return jsonify({'ap': ap_schema.dump(ap)})              


#TODO: does this route really make sense? maybe we should remove it
@aps.route('/<mac>', methods=['PUT'])
@login_required
def update_ap(mac):
    """Update access point"""
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
    """
    Deleting an AP means all its discoveries will also be deleted if the foreign key constraints
    are enforced correctly.
    """
    ap = AccessPoint.query.filter_by(mac=mac).first_or_404()

    db.session.delete(ap)
    db.session.commit()

    return jsonify({'message': 'AP has been deleted.'})

#################################################DISCOVERIES######################################



@aps.route('', methods=['POST'])
@login_required
def add_discovery():
    """
    Add a discovery for the Access Point with MAC address <mac> 
    If there is no corresponding Access Point for this discovery, a new AP is also created in the process.
    """

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
        ap = AccessPoint(mac=discovery.access_point_mac)
        ap.update(discovery)

        try:
            db.session.add(ap)
            db.session.commit()
        except exc.IntegrityError as e:
            return jsonify({'message': 'Integrity error occured when adding AP.'}), 400
    
    #as foreign key we can use the current user object
    discovery.sniffer_id = g.current_user.id
    #set the AP of this discovery
    discovery.access_point = ap

    try:
        db.session.add(discovery)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured when adding discovery.'}), 400

    return jsonify({'message': 'New discovery was added.'})


@aps.route('/<mac>/<discovery_id>', methods=['DELETE'])
@login_required
def delete_discovery(mac, discovery_id):
    """
    Delete a single discovery of an AP. Does not mean the AP will be deleted even if it is 
    the last discovery left of this AP (TODO).
    """
    dis = Discovery.query.filter_by(id=discovery_id).first_or_404()

    db.session.delete(dis)
    db.session.commit()

    return jsonify({'message': 'Discovery has been deleted.'})


@aps.route('/*', methods=['GET'])
@login_required
def get_all_discoveries():
    """
    Show all discoveries. Primarily intended for debugging.
    """

    discoveries = Discovery.query.all()
    return jsonify({'discoveries': discoveries_schema.dump(discoveries)})