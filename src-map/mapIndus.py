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
    
    continent = 'asia'

    importlib.reload(tools)
    
    if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
    elif continent == 'asia':
        xminAll,xmaxAll = -1.315e7, -6.e4
        yminAll,ymaxAll = -1.79e6, 7.93e6
        crs_here = 'epsg:3832'
     
    #borders
    indir = '/mnt/dataEstrella/WII/Boundaries/'
    if continent == 'europe':
        bordersNUTS = gpd.read_file(indir+'NUTS/NUTS_RG_01M_2021_4326.geojson')
        bordersNUST = bordersNUTS.to_crs(crs_here)
        extraNUTS = gpd.read_file(indir+'noNUTS.geojson')
        extraNUST = extraNUTS.to_crs(crs_here)
        bordersSelection = pd.concat([bordersNUST,extraNUST])
    elif continent == 'asia':
        bordersSelection = gpd.read_file(indir+'mask_{:s}.geojson'.format(continent))

    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    landNE = landNE.to_crs(crs_here)


    #industrial zon
    indir = '/mnt/dataEstrella/WII/IndustrialZone/{:s}/'.format(continent)
    indusFiles = sorted(glob.glob(indir+'*.geojson'))

    dirout = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
    
    if not(os.path.isfile(dirout+'industrialZone_osmSource.geojon')):
        indusAll = None
        for indusFile in indusFiles:

            print(os.path.basename(indusFile))
            indus = gpd.read_file(indusFile)
            indus = indus.to_crs(crs_here)

            indus['area_ha'] = indus['geometry'].area/ 10**4
            indus = indus[indus['area_ha']>1]

            if indusAll is None:
                indusAll = indus
            else: 
                indusAll = pd.concat([indusAll,indus])

        indusAll.to_file(dirout+'industrialZone_osmSource.geojon',driver='GeoJSON')
    else: 
        indusAll = gpd.read_file(dirout+'industrialZone_osmSource.geojon')

    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')
    bordersSelection.buffer(-10000)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None')

    indusAll.plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2)
    ax.set_xlim(xminAll,xmaxAll)
    ax.set_ylim(yminAll,ymaxAll)
    ax.set_title('Industrial Area')
    fig.savefig(dirout+'industrialArea_OSM.png',dpi=200)
    plt.close(fig)
