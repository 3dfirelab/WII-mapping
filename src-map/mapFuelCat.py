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
import matplotlib.colors as colors

#homebrewed
import tools
sys.path.append('../src-load/')
glc = importlib.import_module("load-glc-category")

if __name__ == '__main__':
    continent = 'asia'
    
    importlib.reload(tools)
    
    if continent == 'europe':
        xminEU,xmaxEU = 2500000., 7400000.
        yminEU,ymaxEU = 1400000., 5440568.
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


    dirout = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
    
    colorCat=['darkgreen', 'fuchsia', 'gold', 'tomato' ,'teal']
    color_dict = {'vegetation category 1':colorCat[0], 
                  'vegetation category 2':colorCat[1],
                  'vegetation category 3':colorCat[2],
                  'vegetation category 4':colorCat[3],
                  'vegetation category 5':colorCat[4], }
    
    idxclc = range(1,6)
    
    if continent == 'europe':
        #CLC cat
        print('load clc ...', end='')
        sys.stdout.flush()
        indir = '/mnt/dataEstrella/WII/FuelCategories-CLC/{:s}/'.format(continent)
        #idxclc = [1]
        #print('  *** warning: only load cat 1 ***' )
        fuelCat_all = []
        for iv in idxclc:
            fuelCat_ = gpd.read_file(indir+'fuelCategory{:d}.geojson'.format(iv))
            fuelCat_ = fuelCat_.to_crs('epsg:3035')
            fuelCat_['rank'] = 'vegetation category {:d}'.format(iv)

            fuelCat_all.append(fuelCat_)

        fuelCat_all = pd.concat(fuelCat_all)
        print(' done')

    elif continent == 'asia':
        indir = '/mnt/dataEstrella/WII/CLC/'
        to_latlon = pyproj.Transformer.from_crs(crs_here, 'epsg:4326')
        lowerCorner = to_latlon.transform(xminAll, yminAll)
        upperCorner = to_latlon.transform(xmaxAll, ymaxAll)
        fuelCat_all = []
        for iv in idxclc:  
            fuelCat_ = glc.clipped_fuelCat_raster(indir, iv, crs_here, lowerCorner[1], lowerCorner[0], upperCorner[1], upperCorner[0])
            fuelCat_all.append(fuelCat_)
            
            sys.exit()
 

    #plot
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')
    bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None')

    if type(fuelCat) is gpd.geodataframe.GeoDataFrame:
        fuelCat_all.plot(ax=ax, column='rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())))
    else: 
        sys.exit()


    ax.set_xlim(xminEU,xmaxEU)
    ax.set_ylim(yminEU,ymaxEU)
    ax.set_title('Fuel Categories Area')
    
    fig.savefig(dirout+'FuelCatArea_CLC.png',dpi=200)
    plt.close(fig)
