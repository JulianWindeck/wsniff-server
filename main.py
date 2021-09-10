from server import create_server
from server.config import DevelopmentConfig, ProductionConfig

#if you want to use this for production, just change it to ProductionConfig
#or don't provide an argument since it will be a production config by default
server = create_server(DevelopmentConfig)

if __name__ == '__main__':
    server.run(host="0.0.0.0", threaded=True, port=4242)