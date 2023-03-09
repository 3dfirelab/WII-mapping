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
import pyproj
from fiona.crs import from_epsg

#homebrewed
import tools

if __name__ == '__main__':
    importlib.reload(tools)
   
    continent = 'europe'
    xminAll,xmaxAll = 2500000., 7400000.
    yminAll,ymaxAll = 1400000., 5440568.
    crs_here = 'epsg:3035'
    
    #borders
    indir = '/mnt/dataEstrella/WII/Boundaries/'
    bordersNUTS = gpd.read_file(indir+'NUTS/NUTS_RG_01M_2021_4326.geojson')
    bordersNUST = bordersNUTS.to_crs('epsg:3035')
    extraNUTS = gpd.read_file(indir+'noNUTS.geojson')
    extraNUST = extraNUTS.to_crs('epsg:3035')
    bordersSelection = pd.concat([bordersNUST,extraNUST])

    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    landNE = landNE.to_crs('epsg:3035')
    
    #load graticule
    gratreso = 15
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))
    graticule = graticule.to_crs(crs_here)


    dirout = '/mnt/dataEstrella/WII/Maps-Product/'
    
    colorCat=['tab:red', 'tab:orange', 'tab:pink', 'tab:purple' ,'tab:brown', 'tab:cyan' ,'tab:blue']
    color_dict = {'hazard category 1':colorCat[0], 
                  'hazard category 2':colorCat[1],
                  'hazard category 3':colorCat[2],
                  'hazard category 4':colorCat[3],
                  'hazard category 5':colorCat[4],
                  'hazard category 6':colorCat[5],
                  'hazard category 7':colorCat[6], }
    
    #CLC cat
    print('load clc ...', end='')
    sys.stdout.flush()
    indir = '/mnt/dataEstrella/WII/FuelCategories-CLC/{:s}/'.format(continent)
    #idxclc = [1]
    #print('  *** warning: only load cat 1 ***' )
    idxclc = range(1,6)
    fuelCat_all = []
    for iv in idxclc:
        fuelCat_ = gpd.read_file(indir+'fuelCategory{:d}.geojson'.format(iv))
        fuelCat_ = fuelCat_.to_crs('epsg:3035')
        fuelCat_['ICat'] = iv
        fuelCat_['rank'] = 'vegetation category {:d}'.format(iv)

        fuelCat_all.append(fuelCat_)

    fuelCat_all = pd.concat(fuelCat_all)
    print(' done')

    fuelCat_all['IAI'] = -999
    fuelCat_all.loc[(fuelCat_all['AI']>0.9)                         ,'IAI'] = 0
    fuelCat_all.loc[(fuelCat_all['AI']>0  )&(fuelCat_all['AI']<=0.9),'IAI'] = 1
    fuelCat_all.loc[(fuelCat_all['AI']<=0 )                         ,'IAI'] = 2 # to update to pass it to ==0. need PoverA update. 

    fuelCat_all['IFH'] = fuelCat_all['ICat'] + fuelCat_all['IAI']
    fuelCat_all['FH_rank'] = 'hazard category ' + fuelCat_all['IFH'].astype(str)



    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    fuelCat_all.plot(ax=ax, column='FH_rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())),zorder=4)
    
    ax.set_xlim(xminAll,xmaxAll)
    ax.set_ylim(yminAll,ymaxAll)

    #set axis
    bbox = shapely.geometry.box(xminAll, yminAll, xmaxAll, ymaxAll)
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(crs_here.split(':')[1]))
    geo['geometry'] = geo.boundary
    ptsEdge =  gpd.overlay(graticule, geo, how = 'intersection', keep_geom_type=False)
    
    lline = shapely.geometry.LineString([[xminAll,ymaxAll],[xmaxAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=from_epsg(crs_here.split(':')[1]))
    ptsEdgelon =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
    
    ax.xaxis.set_ticks(ptsEdgelon.geometry.centroid.x)
    ax.xaxis.set_ticklabels(ptsEdgelon.display)
    ax.xaxis.tick_top()
    
    lline = shapely.geometry.LineString([[xminAll,yminAll],[xminAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=from_epsg(crs_here.split(':')[1]))
    ptsEdgelat =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)

    ax.yaxis.set_ticks(ptsEdgelat.geometry.centroid.y)
    ax.yaxis.set_ticklabels(ptsEdgelat.display)

    ax.set_title('Fire Hazard Categories Area', pad=30)
    
    fig.savefig(dirout+'FireHazardCatArea.png',dpi=200)
    plt.close(fig)
