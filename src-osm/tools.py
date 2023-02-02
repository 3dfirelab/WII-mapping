import geopandas as gpd
import shapely 

from matplotlib import pyplot as plt
import geopandas as gpd
from shapely.geometry import Polygon


def dissolveGeometryWithinBuffer(gdf,bufferSize = 20.):

    gdf['geometry'] = gdf.geometry.apply(lambda g: g.buffer(bufferSize))

    s_ = gpd.GeoDataFrame(geometry=[gdf.unary_union]).explode( index_parts=False ).reset_index( drop=True )

    s_ = s_.geometry.apply(lambda g: g.buffer(-1*bufferSize))

    return s_

def getDistanceBetweenGdf(gdf1,gdf2):
    return gdf1.geometry.apply(lambda g: gdf2.distance(g))


if __name__ == '__main__':

    indir = '/mnt/dataEstrella/OSM/'
    wood = gpd.read_file(indir+'wood.shp')

    wood_geom = dissolveGeometryWithinBuffer(wood)

    distancesIntraWood = getDistanceBetweenGdf(wood_geom,wood_geom)
    
