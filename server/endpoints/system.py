from flask import request, jsonify, make_response, current_app as app, Blueprint
from werkzeug.security import check_password_hash

from server.models import User
from server.login import generate_token 


system = Blueprint('system', __name__)

#normal 404-errorhandler would return a http-site
#for our api we prefer a JSON message
@system.app_errorhandler(404)
def page_not_found(error):
    resp = jsonify({'message': 'Not found.',
                    'error': str(error)})
    resp.status_code = 404
    return resp

@system.app_errorhandler(400)
def bad_request(error):
    resp = jsonify({'message': 'Bad Request.',
                    'error': str(error)})
    resp.status_code = 400
    return resp


@system.route('/')
@system.route('/<path:p>')
def home(p='/'):
    return jsonify({
        'path': p
    })


@system.route('/availability', methods=['GET', 'POST'])
def is_available():
    """
    Should be used to check with wsniff client whether the server is currently available
    The client should send a JSON message {'message': 'ping'} to which the server responds
    with {'message': 'pong'}
    """
    data = request.get_json()
    #actually we don't check whether the message sent here is 'ping' since it is unnessary
    #but it would be nice if you do :)
    if not data or not data.get('message'):
        return jsonify({'message': 'Please send me a "ping" message.'}), 400
    
    return jsonify({'message': 'pong'}), 200


@system.route('/login')
def login():
    auth = request.authorization

    #authetication information is missing
    if not (auth and auth.username and auth.password):
        return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

    #for this to work the username would have to be unique
    user = User.query.filter_by(name=auth.username).first()

    #if there is no user with that username
    if not user:
        return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

    #password is not correct
    if not check_password_hash(user.password, auth.password):
        return make_response('Could not verify!', 401, {'WWW-Authenticate' : 'Basic realm="Login Required"'})

    #if everything is fine, generate a token and return it
    token = generate_token(user)
    return jsonify({'token': token})