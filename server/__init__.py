from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

from server.config import ProductionConfig

import uuid

db = SQLAlchemy()
ma = Marshmallow()


def create_server(config_class=ProductionConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    #order matters here: SQLAlchemy has to be initialized before Marshmallow
    ma.init_app(app)
    
    #add endpoints
    from server.endpoints.system import system
    from server.login import login
    from server.endpoints.users import users
    from server.endpoints.maps import maps
    from server.endpoints.access_point import aps
     

    app.register_blueprint(system)
    app.register_blueprint(login)
    app.register_blueprint(users)
    app.register_blueprint(maps)
    app.register_blueprint(aps)
    

    return app