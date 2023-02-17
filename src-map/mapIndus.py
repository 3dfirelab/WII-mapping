import sys
import os 
import pandas as pd
import geopandas as gpd
import shapely 
import glob
from matplotlib import pyplot as plt
from shapely.geometry import Polygon
import importlib
import warnings
import pyproj

#homebrewed
import tools

if __name__ == '__main__':
    importlib.reload(tools)
    
    '''
    lonminEU,latminEU, lonmaxEU,latmaxEU = [-26., 30, 99.52727619009086, 80.51193780175987]
    from_latlon = pyproj.Transformer.from_crs('epsg:4326', 'epsg:3035' )
    xminEU,yminEU = from_latlon.transform(latminEU,lonminEU)
    xmaxEU,ymaxEU = from_latlon.transform(latmaxEU,lonmaxEU ) 
    '''
    xminEU,xmaxEU = 2500000., 7400000.
    yminEU,ymaxEU = 1400000., 5440568.
    
    
    #lonminEU,latminEU, lonmaxEU,latmaxEU = [-26., 30, 99.52727619009086, 80.51193780175987]
    #from_latlon = pyproj.Transformer.from_crs('epsg:4326', 'epsg:3035' )
    #xminEU,yminEU = from_latlon.transform(latminEU,lonminEU)
    #xmaxEU,ymaxEU = from_latlon.transform(latmaxEU,lonmaxEU ) 
    
    #borders
    indir = '/mnt/dataEstrella/WII/Boundaries/'
    bordersNUTS = gpd.read_file(indir+'NUTS/NUTS_RG_01M_2021_4326.geojson')
    bordersNUST = bordersNUTS.to_crs('epsg:3035')
    extraNUTS = gpd.read_file(indir+'noNUTS.geojson')
    extraNUST = extraNUTS.to_crs('epsg:3035')

    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    landNE = landNE.to_crs('epsg:3035')

    bordersNUTSm = pd.concat([bordersNUST,extraNUST])

    #industrial zon
    indir = '/mnt/dataEstrella/WII/IndustrialZone/'
    indusFiles = sorted(glob.glob(indir+'*.geojson'))

    dirout = '/mnt/dataEstrella/WII/Maps-Product/'
    
    if not(os.path.isfile(dirout+'industrialZone_osmSource.geojon')):
        indusEU = None
        for indusFile in indusFiles:

            print(os.path.basename(indusFile))
            indus = gpd.read_file(indusFile)
            indus = indus.to_crs('epsg:3035')

            indus['area_ha'] = indus['geometry'].area/ 10**4
            indus = indus[indus['area_ha']>1]

            if indusEU is None:
                indusEU = indus
            else: 
                indusEU = pd.concat([indusEU,indus])

        indusEU.to_file(dirout+'industrialZone_osmSource.geojon',driver='GeoJSON')
    else: 
        indusEU = gpd.read_file(dirout+'industrialZone_osmSource.geojon')

    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')
    bordersNUTSm[bordersNUTSm['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None')

    indusEU.plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2)
    ax.set_xlim(xminEU,xmaxEU)
    ax.set_ylim(yminEU,ymaxEU)
    ax.set_title('Industrial Area')
    fig.savefig(dirout+'industrialArea_OSM.png',dpi=200)
    plt.close(fig)
