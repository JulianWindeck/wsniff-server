import math


#can be used for converting [degree] to [rad] by multiplying the degree value with this constant
#since 1degree = pi/180 rad = 0.01745
degree_rad_const = 0.01745

class Point():
    """
    Used to represent a point on our earth
    """
    def __init__(self, lat, lon):
        """
        lat: latitude in degrees
        lon: longitude in degrees
        """
        self.lat = lat 
        self.lon = lon 

        self.lat_rad = lat * degree_rad_const
        self.lon_rad = lon * degree_rad_const


#mean radius of our globe in [km]
EARTH_RADIUS = 6371.0

def distance_simple(p1, p2):
    """
    It is only accurate for smaller distances.
    However, this might have better performance when computing the distance for a huge number of points
    So use it accordingly
    """

    #distance between 2 lines of latitude is always 111.3
    #but dist between 2 lines of longitude depends on latitude (so take mean of lat values)
    lat = (p1.lat + p2.lat) / 2 * degree_rad_const 

    dy = 111.3 * (p1.lat - p2.lat)
    dx = 111.3 * math.cos(lat) * (p1.lon - p2.lon)
    
    return math.sqrt(dx**2 + dy**2)

def distance_accurate(p1, p2):
    """
    Relatively good approximation, even for huge distances
    For small distances, consider using 'distance_simple'
    """
    #angle between p1 and p2 with the north pole
    angle = math.acos(math.sin(p1.lat_rad)*math.sin(p2.lat_rad) + math.cos(p1.lat_rad)*math.cos(p2.lat_rad)*math.cos(p2.lon_rad-p1.lon_rad))

    #this is distance between p1 and p2
    return EARTH_RADIUS * angle


#good explanation: https://www.kompf.de/gps/distcalc.html

if __name__ == '__main__':
    p1 = Point(49.59756231314638, 11.006192586321422)
    p2 = Point(49.59763663303554, 11.006168446099961)
    print(distance_simple(p1, p2))
    print(distance_accurate(p1, p2))
    #should be 132,72 km