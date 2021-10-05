from configparser import ConfigParser

class Config:
    SECRET_KEY = "changethisforproduction"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

#note that if really used in a production environment, a wsgi
#server (e.g. gunicorn in combination with nginx) should be used
#instead of the default flask webserver
class ProductionConfig(Config):
    DEBUG = False
    #this is Flasks default, since it helps with caching
    JSON_SORT_KEYS = True

class DevelopmentConfig(Config):
    DEBUG = True
    #for better readability (JSON content is ordered corresponding to marshmallow declaration)
    JSON_SORT_KEYS = False