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

# N to M relationship between sniffers and wardriving maps which they helped creating
participate_in = db.Table(
    'participate_in',
    db.Column('map_id', db.Integer, db.ForeignKey('wardriving_map.id'), primary_key=True),
    db.Column('sniffer_id', db.Integer, db.ForeignKey('sniffer.id'), primary_key=True)
)

class Encryption():
    OPEN = 0
    WEP = 1
    WPA = 2
    WPA2 = 3

class AccessPoint(db.Model):
    __tablename__ = 'access_point'

    #Of course, it of makes sense to use the MAC address as the primary key.
    #But for better performance, we don't want to store it as a string but rather
    #interpret it as an integer:
    #e.g. 00-80-41-ae-fd-7e -> 0x008041AEFD7E and convert this hex number to decimal
    mac = db.Column(db.Integer, primary_key=True)

    #a SSID has a max length of 32 characters, but we intentionally drop that constraint
    #to be open for changes
    last_ssid = db.Column(db.String(64))

    #these are derived values we could also compute using a join with the discovery table
    #but for performance issues we allow a little bit redundance
    t_last_seen = db.Column(db.DateTime, nullable=False)
    last_encryption = db.Column(db.Integer, nullable=False)
    #the last channel this AP was seen on
    last_channel = db.Column(db.Integer, nullable=False)

    gps_lat = db.Column(db.Float, nullable=False)
    gps_lon = db.Column(db.Float, nullable=False)

    #all the wardriving maps this AP is part of
    # maps = db.relationship('WardrivingMap', secondary=part_of, back_populates='access_points')

    #the different occurrences this AP was discovered
    discoveries = db.relationship('Discovery', back_populates='access_point')

    #attributes of this AP which were added at runtime by a user
    attributes = db.relationship('AP_EAV', back_populates='access_point')

    def update(self, discovery):
        """
        Update all the values of the AP with the new information of this discovery.

        WARNING: you still have to call session.add(ap) and commit() to apply these changes to the DB!
        """
        #WARNING: don't try to add the discovery to the list of this AP's discoveries here since it 
        #will complicate things unneccessarily

        #update values
        self.last_ssid = discovery.ssid
        self.t_last_seen = discovery.timestamp
        self.last_encryption = discovery.encryption
        self.last_channel = discovery.channel
        #you could also directly compute a better approximation with the values of all discoveries
        #(signal_stregths and gps values) here
        self.gps_lat = discovery.gps_lat
        self.gps_lon = discovery.gps_lon


class AP_EAV(db.Model):
    """
    Used to add attributes to access points dynamiccaly during runtime without 
    the need for schema modification.
    """
    mac = db.Column(db.Integer, db.ForeignKey('access_point.mac', ondelete='CASCADE'), primary_key=True) 
    attribute = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text)
    type = db.Column(db.String(32))

    access_point = db.relationship('AccessPoint', back_populates='attributes')

    #NOTE: the corresponding POST route for adding AP_EAV objects has to place 
    #fitting restrictions on the type
    def get_value(self):
        if type == "Integer":
            return int(self.value)
        if type == "Real":
            return float(self.value)
        else:
            return self.value


#an AP can be discovered by multiple sniffers - we want to keep track of all occurances 
class Discovery(db.Model):
    __tablename__ = 'discovery'

    #discovery should be a weak entity type, so the existance of its entities depends on 
    #the existance of the corresponding AP entities 
    #(this should be part of the primary key if modelled correctly, but there are conflicts with some DBMS)
    access_point_mac = db.Column(db.Integer, db.ForeignKey('access_point.mac', ondelete='CASCADE'), nullable=False)
   
    #this should be a partial key but some DBS don't support autoincrement when using composite keys
    id = db.Column(db.Integer, primary_key=True)

    #don't place any constraints on the channel since the numbers can differ from country to country
    channel = db.Column(db.Integer, nullable=False)
    encryption = db.Column(db.Integer, nullable=False)
    #this is the maximum RSSI the sniffer got during the timespan he saw the AP
    signal_strength = db.Column(db.Integer, nullable=False)

    ssid = db.Column(db.String(64))
    
    timestamp = db.Column(db.DateTime, nullable=False)
    #gps data: latitude and longitude when the sniffer had the highest signal strength
    #(and was therefore closest to the AP)
    gps_lat = db.Column(db.Float, nullable=False)
    gps_lon = db.Column(db.Float, nullable=False)
    
    #the sniffer which made this discovery
    sniffer_id = db.Column(db.Integer, db.ForeignKey('sniffer.id'), nullable=False)
    sniffer = db.relationship('Sniffer', back_populates='discoveries')

    #the map of which this discovery is a part 
    map_id = db.Column(db.Integer, db.ForeignKey('wardriving_map.id', ondelete='CASCADE'), nullable=False)
    map = db.relationship('WardrivingMap', back_populates='discoveries')

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

    #all discoveries that were made creating this map
    discoveries = db.relationship('Discovery', back_populates='map', cascade="all, delete")

    #all access points we found
    # access_points = db.relationship('AccessPoint', secondary=part_of, back_populates='maps')

    #further generic attributes
    attributes = db.relationship('Map_StringEAV', back_populates='map')

    def __repr__(self):
        return f"Map('{self.id}', '{self.title}')"

class Map_StringEAV(db.Model):
    """
    Generic table that can be used to dynamically add metadate/attributs to maps without 
    having to add columns to the WardrivingMap table. Follows the principle of deferred design.
    """
    #these to form the primary key. if attributes with multiple values were to be supported
    #you could add another column id to the primary key
    map_id = db.Column(db.Integer, db.ForeignKey('wardriving_map.id', ondelete='CASCADE'), primary_key=True) 
    attribute = db.Column(db.String(64), primary_key=True)
    
    value = db.Column(db.Text)

    map = db.relationship('WardrivingMap', back_populates='attributes')
    