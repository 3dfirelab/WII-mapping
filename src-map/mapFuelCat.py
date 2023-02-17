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


    dirout = '/mnt/dataEstrella/WII/Maps-Product/'
    
    colorCat=['darkgreen', 'fuchsia', 'gold', 'tomato' ,'teal']
    color_dict = {'vegetation category 1':colorCat[0], 
                  'vegetation category 2':colorCat[1],
                  'vegetation category 3':colorCat[2],
                  'vegetation category 4':colorCat[3],
                  'vegetation category 5':colorCat[4], }
    
    #CLC cat
    print('load clc ...', end='')
    sys.stdout.flush()
    indir = '/mnt/dataEstrella/WII/FuelCategories-CLC/'
    #idxclc = [1]
    #print('  *** warning: only load cat 1 ***' )
    idxclc = range(1,6)
    fuelCat_all = []
    for iv in idxclc:
        fuelCat_ = gpd.read_file(indir+'fuelCategory{:d}.geojson'.format(iv))
        fuelCat_ = fuelCat_.to_crs('epsg:3035')
        fuelCat_['rank'] = 'vegetation category {:d}'.format(iv)

        fuelCat_all.append(fuelCat_)

    fuelCat_all = pd.concat(fuelCat_all)
    print(' done')

    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')
    bordersNUTSm[bordersNUTSm['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None')

    fuelCat_all.plot(ax=ax, column='rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())))
    
    ax.set_xlim(xminEU,xmaxEU)
    ax.set_ylim(yminEU,ymaxEU)
    ax.set_title('Fuel Categories Area')
    
    fig.savefig(dirout+'FuelCatArea_CLC.png',dpi=200)
    plt.close(fig)
