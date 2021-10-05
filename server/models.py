from datetime import datetime
from server import db


"""
This module comprises the ORM-layer, meaning how our database tables should look like
"""

#this acts as a baseclass which is used for authetication to the API
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    #used to hide the DB id when accessing the API
    public_id = db.Column(db.String(50), unique=True, nullable=False)
    
    name = db.Column(db.String(50), nullable=False, unique=True)
    #hash (sha256) of this user's password
    password = db.Column(db.String(88), nullable=False)
    
    #flag indicating whether this user has admin priviledges
    #used for the @admin_required route decorator
    admin = db.Column(db.Boolean, default=False, nullable=False)

    #discriminator column which is used for indicating the type of object represented within this row
    type = db.Column(db.String(50))
    __mapper_args__ = {
        'polymorphic_identity':'user',
        'polymorphic_on':type
    }

    def __str__(self):
        return f"User<{self.id}: {self.name} admin={self.admin}>"

#relationship between sniffers and wardriving maps which they helped creating
participate_in = db.Table(
    'participate_in',
    db.Column('map_id', db.Integer, db.ForeignKey('wardriving_map.id'), primary_key=True),
    db.Column('sniffer_id', db.Integer, db.ForeignKey('sniffer.id'), primary_key=True)
)

#relationship type between WardrivingMap and AccessPoint,
#to store which APs should be displayed in which maps
part_of = db.Table(
    'part_of', 
    db.Column('map_id', db.Integer, db.ForeignKey('wardriving_map.id'), primary_key=True), 
    db.Column('access_point_id', db.Integer, db.ForeignKey('access_point.mac'), primary_key=True)
)


class Encryption():
    OPEN = 0
    WEP = 1
    WPA = 2
    WPA2 = 3

class AccessPoint(db.Model):
    __tablename__ = 'access_point'

    #it of course makes sense to use the MAC address as the primary key
    #for better performance, we don't want to store it as a string but rather
    #interpret it as an integer:
    #e.g. 00-80-41-ae-fd-7e -> 0x008041AEFD7E and convert this hex number to decimal
    mac = db.Column(db.Integer, primary_key=True)

    #a SSID has a max length of 32 characters, but we intentionally drop that constraint
    #to be open for changes
    ssid = db.Column(db.String(64))

    #these are derived values we could also compute using a join with the discovery table
    #but for performance issues we allow a little bit redundance
    t_last_seen = db.Column(db.DateTime, nullable=False)
    last_encryption = db.Column(db.Integer, nullable=False)
    #the last channel this AP was seen on
    last_channel = db.Column(db.Integer, nullable=False)

    #all the wardriving maps this AP is part of
    maps = db.relationship('WardrivingMap', secondary=part_of, back_populates='access_points')

    #the different occurrences this AP was discovered
    discoveries = db.relationship('Discovery', back_populates='access_point')


    

#an AP can be discovered by multiple sniffers - we want to keep track of all occurances 
class Discovery(db.Model):
    __tablename__ = 'discovery'

    #discovery should be a weak entity type, so the existance of its entities depends on 
    #the existance of the corresponding AP entities 
    #(this should be part of the primary key if modelled correctly, but there are conflicts with some DBMS)
    access_point_mac = db.Column(db.Integer, db.ForeignKey('access_point.mac', ondelete='CASCADE'))
   
    #this should be a partial key but some DBS don't support autoincrement when using composite keys
    id = db.Column(db.Integer, primary_key=True)

    #don't place any constraints on the channel since the numbers can differ from country to country
    channel = db.Column(db.Integer, nullable=False)
    encryption = db.Column(db.Integer, nullable=False)
    #this is the maximum RSSI the sniffer got during the timespan he saw the AP
    signal_stregth = db.Column(db.Integer, nullable=False)
    
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    #gps data: latitude and longitude when the sniffer had the highest signal strength
    #(and was therefore closest to the AP)
    gps_lat = db.Column(db.Float, nullable=False)
    gps_lon = db.Column(db.Float, nullable=False)
    
    #the sniffer which made this discovery
    sniffer_id = db.Column(db.Integer, db.ForeignKey('sniffer.id'), nullable=False)
    sniffer = db.relationship('Sniffer', back_populates='discoveries')

    #the access point this discovery belongs to
    access_point = db.relationship('AccessPoint', back_populates='discoveries')


#Sniffer inherits from User, so a sniffer can authenticate just like a regular user
class Sniffer(User):
    __tablename__ = 'sniffer'

    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    #since Sniffer is a subclass of User, we need to define a value for the discriminator column
    __mapper_args__ = {
        'polymorphic_identity':'sniffer',
    }

    #everything the sniffer found out
    discoveries = db.relationship('Discovery', back_populates='sniffer') 

    #all maps the sniffer contributed to 
    maps = db.relationship('WardrivingMap', secondary=participate_in, back_populates='sniffers')

class WardrivingMap(db.Model):
    __tablename__ = 'wardriving_map'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    desc = db.Column(db.Text, nullable=True)

    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    #sniffers that contributed to this map
    sniffers = db.relationship('Sniffer', secondary=participate_in, back_populates='maps')

    #all access points we found
    access_points = db.relationship('AccessPoint', secondary=part_of, back_populates='maps')

    def __repr__(self):
        return f"Capture('{self.id}', '{self.title}')"