import sys
import os 
#os.environ['USE_PYGEOS'] = '0'
import pandas as pd 
import geopandas as gpd
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
import pyproj
import rasterio
import shapely
from fiona.crs import from_epsg
from rasterio.mask import mask
import pdb 

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def clipped_fuelCat_gdf(indir, outdir, iv, crs, xminContinent,yminContinent, xmaxContinent,ymaxContinent):

    #print('fuel global lc')
    fuelCatTag = []
    fuelCatTag.append([111,113,121,123]) #1
    fuelCatTag.append([115,116,125,126]) #2
    fuelCatTag.append([112,114,122,124,20,30]) #3
    fuelCatTag.append([90]) #4
    fuelCatTag.append([100]) #5

    filein = indir + 'PROBAV_LC100_global_v3.0.1_2018-conso_Discrete-Classification-map_EPSG-4326.tif' 

    gdflc = None
    with rasterio.open(filein) as src:
        
        #clip
        bbox = shapely.geometry.box(xminContinent,yminContinent, xmaxContinent,ymaxContinent)
        geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))
        #geo = geo.to_crs(crs=src.crs.data)
        coords = getFeatures(geo)
        data_, out_transform = mask(src, shapes=coords, crop=True)

        #print ('fuelCat ', iv, end='')
        condition =  (data_!=fuelCatTag[iv-1][0])
        if len(fuelCatTag[iv-1]) > 1:
            for xx in fuelCatTag[iv-1][1:]:
                condition &= (data_!=xx)
        data_masked = np.ma.masked_where(condition,data_)
        
        if not(False in data_masked.mask): return None

        #print (' -- array loaded')
        # Use a generator instead of a list
        shape_gen = ((shapely.geometry.shape(s), v) for s, v in rasterio.features.shapes(data_masked, transform=out_transform))

        # either build a pd.DataFrame
        # df = DataFrame(shape_gen, columns=['geometry', 'class'])
        # gdf = GeoDataFrame(df["class"], geometry=df.geometry, crs=src.crs)

        # or build a dict from unpacked shapes
        gdf = gpd.GeoDataFrame(dict(zip(["geometry", "class"], zip(*shape_gen))), crs=src.crs)

        return gdf.to_crs(crs)


if __name__ == '__main__':

    continent = 'asia'
    
    if continent == 'europe':
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [-31., 24.505457173625324, 99.52727619009086, 80.51193780175987]
    elif continent == 'asia':
        #xminContinent,yminContinent, xmaxContinent,ymaxContinent = [28.7, -14.9, 188, 87.]
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [124.613617-1,  33.197577+1,  131.862522-1,  38.624335+1 ] 

    categories = np.arange(1,6)
    indir = '/mnt/dataEstrella/WII/CLC/'
    outdir = '/mnt/dataEstrella/WII/FuelCategories-CLC/{:s}/'.format(continent)

    for iv in categories:

        gdf = clipped_fuelCat_gdf(indir, outdir, iv, xminContinent,yminContinent, xmaxContinent,ymaxContinent)
        if gdf is not None: 
            gdf.to_file(outdir+'fuelCategory{:d}.geojson'.format(iv), driver="GeoJSON")



