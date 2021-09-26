from flask import jsonify, g, request, Blueprint, current_app as app

from server.models import User

import jwt
import datetime
from functools import wraps


login = Blueprint('login', __name__)

#before each request, the token (if present) should be obtained from the HTTP-header
#and stored in the global g variable
@login.before_app_request
def load_token():
    """
    flask.g is a namespace object that can store data during one request from one function to antoher,
    working also in threaded environments
    """
    g.token = None
    if 'x-access-token' in request.headers:
        g.token = request.headers['x-access-token']


#when a new client should be registered, you want to generate a new token
def generate_token(user, valid_duration=24):
    """
    this function will generate a JWT token
    valid_duration: hours in which the token will expire
    """
    token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)}, app.config['SECRET_KEY'], algorithm="HS256")
    return token


################################## decorators that can be used for routes ###########################

def login_required(f):
    """
    Use this decorator when a route should require to be logged in
    as a registered user. Inside a corresponding function, you can
    access the current user object with 'g.current_user'.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(g.token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.current_user = User.query.filter_by(public_id=data['public_id']).first()

            if not g.current_user:
                raise Exception()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        #every function that gets decorated with 'login_required' will need a user object
        #as its first parameter
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    You can treat this decorator like login_required with an additional permission check.
    Use this decorator for a route that requires the client to be a logged in user
    with admin priviledges.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(g.token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.current_user = User.query.filter_by(public_id=data['public_id']).first()
            
            if not g.current_user:
                raise Exception()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        #after this, you can access the current_user object
        if not g.current_user.admin:
            return jsonify({'message': 'You don\'t have the permission to do that!'}), 403

        #every function that gets decorated with 'login_required' will need a user object
        #as its first parameter
        return f(*args, **kwargs)

    return decorated