from marshmallow import fields

from server import ma
from server.models import AccessPoint, Discovery, WardrivingMap, User, Sniffer, Map_StringEAV, AP_EAV

"""
Here are all API definitions, meaning that 
it is defined how the output and valid input of our API should look like.
"""

#already define this here and complete it later in order to prevent a NameError
#since we have cyclic class dependencies here (because we need class names for fields.Nested)
class MapSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = WardrivingMap
class DiscoverySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Discovery


###################################USER RELATED###################################################

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        #makes sure a DB-Model object created when calling [schema].load()
        load_instance = True
        #fields to exclude (entirely/when producing JSON output/when parsing incoming data)
        exclude=[]
        load_only = ['password']
        dump_only = ['public_id', 'name']

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class SnifferSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Sniffer
        #makes sure a DB-Model object created when calling [schema].load()
        load_instance = True
        #fields to exclude (entirely/when producing JSON output/when parsing incoming data)
        exclude=['type']
        load_only = ['password']
        dump_only = ['public_id', 'id']
    
    maps = fields.Nested(MapSchema, many=True)
    discoveries = fields.Nested(DiscoverySchema, many=True)

sniffer_schema = SnifferSchema()
sniffers_schema = SnifferSchema(many=True, exclude=['discoveries'])



###################################ACCESS POINT###################################################

class AP_EAV_Schema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AP_EAV
        load_instance = True
        #here the magic is happening: do not dump the DB content ...
        exclude=['type'] #(value is automatically overshadowed by following field)
    
    #TODO: data type is somehow wrong :(
    #... but rather use a method field to output the right data type
    value = fields.Method("get_value")
    def get_value(self, eav_obj):
        #call get_value() method of AP_EAV model object
        return eav_obj.get_value()

class DiscoverySchema(ma.SQLAlchemyAutoSchema):
    
    class Meta:
        model = Discovery
        #makes sure a DB-Model object created when calling [schema].load()
        load_instance = True
        #we also want the mac of the AP (which is part of the primary key) to be sent
        include_fk = True
        #fields to exclude (entirely/when producing JSON output/when parsing incoming data)
        exclude=['sniffer_id', 'map_id']
        load_only = []
        dump_only = ['sniffer']

    sniffer = fields.Nested(SnifferSchema, exclude=['discoveries', 'maps'])
    

discovery_schema = DiscoverySchema()
discoveries_schema = DiscoverySchema(many=True)


class AccessPointSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AccessPoint
        #maintain the field ordering declared here for JSON output
        ordered = True
        #makes sure a DB-Model object created when calling [schema].load()
        load_instance = True
        #fields to exclude (entirely/when producing JSON output/when parsing incoming data)
        exclude=[]
        load_only = []
        dump_only = []
    
    #you don't need to transfer 'access_point_mac' since the mac is already part of the AP itself
    discoveries = fields.Nested(DiscoverySchema, many=True, exclude=['access_point_mac'])
    attributes = fields.Nested(AP_EAV_Schema, many=True)

ap_schema = AccessPointSchema()
#don't display the discoveries when showing multiple access points
aps_schema = AccessPointSchema(many=True, exclude=['discoveries'])


###########################################MAP####################################################

class MapEAVSchema(ma.SQLAlchemyAutoSchema):

    class Meta:
        model = Map_StringEAV


class MapSchema(ma.SQLAlchemyAutoSchema):
    
    class Meta:
        model = WardrivingMap
        #makes sure a DB-Model object created when calling [schema].load()
        load_instance = True
        
        #fields to exclude (entirely/when producing JSON output/when parsing incoming data)
        exclude=[]
        load_only = []
        dump_only = []
    
    sniffers = fields.Nested(SnifferSchema, many=True, exclude=["maps", "discoveries"])
    discoveries = fields.Nested(DiscoverySchema, many=True)
    attributes = fields.Nested(MapEAVSchema, many=True)

map_schema = MapSchema()
maps_schema = MapSchema(many=True, exclude=['discoveries'])

 