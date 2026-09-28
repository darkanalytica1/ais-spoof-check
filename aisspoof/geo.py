import math
R_KM = 6371.0088
def haversine_km(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R_KM*math.asin(min(1.0, math.sqrt(a)))
def point_in_polygon(lon, lat, ring):
    """Ray casting on a single ring [[lon,lat],...]."""
    inside = False; n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]; x2, y2 = ring[(i+1) % n]
        if (y1 > lat) != (y2 > lat):
            xi = x1 + (lat - y1)*(x2 - x1)/((y2 - y1) or 1e-12)
            if lon < xi: inside = not inside
    return inside
def in_multipolygon(lon, lat, geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if point_in_polygon(lon, lat, poly[0]) and not any(point_in_polygon(lon, lat, h) for h in poly[1:]):
            return True
    return False
class Grid:
    """Regular lat/lon elevation grid (e.g. GEBCO) with bilinear lookup. z in metres, >0 = land."""
    def __init__(self, lats, lons, z):
        self.lats, self.lons, self.z = lats, lons, z
        self.dla = lats[1]-lats[0]; self.dlo = lons[1]-lons[0]
    def contains(self, lon, lat):
        return self.lats[0] <= lat <= self.lats[-1] and self.lons[0] <= lon <= self.lons[-1]
    def at(self, lon, lat):
        fi = (lat-self.lats[0])/self.dla; fj = (lon-self.lons[0])/self.dlo
        i = max(0, min(len(self.lats)-2, int(fi))); j = max(0, min(len(self.lons)-2, int(fj)))
        ti, tj = min(1, max(0, fi-i)), min(1, max(0, fj-j)); z = self.z
        return (1-ti)*((1-tj)*z[i][j]+tj*z[i][j+1]) + ti*((1-tj)*z[i+1][j]+tj*z[i+1][j+1])
