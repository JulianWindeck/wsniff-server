from flask import request, jsonify, current_app as app, Blueprint, g
from werkzeug.security import generate_password_hash 
from sqlalchemy import exc
from marshmallow import ValidationError

from server import db
from server.models import User, Sniffer
from server.login import admin_required, login_required
from server.endpoints.api_definition import user_schema, users_schema, sniffer_schema, sniffers_schema

import uuid


users = Blueprint('users', __name__, url_prefix='/users')


###############################################ROUTES########################################

#get all users
@users.route('', methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.all()

    output = users_schema.dump(users)
    return jsonify({'users': output})


@users.route('/<public_id>', methods=['GET'])
@admin_required
def get_one_user(public_id):
    """
    Get one specific user. Only displays user information, also for sniffers.
    If you need sniffer-specific information, please call /sniffers/<id>
    """
    user = User.query.filter_by(public_id=public_id).first_or_404()

    output = user_schema.dump(user)
    return jsonify({'user': output})

@users.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    Returns the information about the user which is currently logged in.
    Can also be used by client to check whether he is autheticated at all.
    """
    return jsonify({'user': user_schema.dump(g.current_user)})


@users.route('/sniffers', methods=['GET'])
@login_required
def get_all_sniffers():
    """
    Get all the sniffer users only.
    """
    sniffers = Sniffer.query.all()
    return jsonify({'sniffers': sniffers_schema.dump(sniffers)})


@users.route('/sniffers/<id>', methods=['GET'])
@login_required
def get_sniffer(id):
    """
    Get one specific sniffer
    """
    sniffer = Sniffer.query.filter_by(id=id).first_or_404()
    return jsonify({'sniffer': sniffer_schema.dump(sniffer)})


@users.route('', methods=['POST'])
@admin_required
def create_sniffer():
    """
    Create a new sniffer
    """
    try: 
        sniffer = sniffer_schema.load(request.get_json())
    except ValidationError as e:
        return jsonify(e.messages), 400

    #create a password hash and store this as the user's password in the DB
    hashed_password = generate_password_hash(sniffer.password, method='sha256')
    sniffer.password = hashed_password

    sniffer.public_id=str(uuid.uuid4())
    try:
        db.session.add(sniffer)
        db.session.commit()
    except exc.IntegrityError as e:
        return jsonify({'message': 'Integrity error occured.'}), 400

    return jsonify({'message': 'New sniffer created.'})


@users.route('/<public_id>', methods=['PUT'])
@admin_required
def change_user_password(public_id):
    """
    Update password (especially needed for admin user)
    """
    user = User.query.filter_by(public_id=public_id).first_or_404()

    try:
        #update existing object 
        user = user_schema.load(request.get_json(), instance=user)
    except ValidationError as e:
       return jsonify(e.messages), 400 

    hashed_password = generate_password_hash(user.password, method='sha256')
    user.password = hashed_password

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User has been updated.'})

@users.route('/<public_id>', methods=['DELETE'])
@admin_required
def delete_user(public_id):
    user = User.query.filter_by(public_id=public_id).first_or_404()

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User has been deleted.'})