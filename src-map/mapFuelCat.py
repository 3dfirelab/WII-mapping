import sys
import os 
import matplotlib as mpl
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
import numpy as np
import earthpy.plot as ep
import pyproj
from fiona.crs import from_epsg
import socket

#homebrewed
import params
import tools
sys.path.append('../src-load/')
glc = importlib.import_module("load-glc-category")


def loadFuelCat(continent, crs_here, xminAll, yminAll, xmaxAll, ymaxAll):

    idxclc = range(1,6)
    
    if continent == 'europe':
        #CLC cat
        print('load clc ...', end='')
        sys.stdout.flush()
        indir = '{:s}FuelCategories-CLC/{:s}/'.format(dir_data,continent)
        #idxclc = [1]
        #print('  *** warning: only load cat 1 ***' )
        fuelCat_all = []
        for iv in idxclc:
            fuelCat_ = gpd.read_file(indir+'fuelCategory{:d}.geojson'.format(iv))
            fuelCat_ = fuelCat_.to_crs(crs_here)
            fuelCat_['rank'] = 'vegetation category {:d}'.format(iv)
            fuelCat_['ICat'] = iv

            fuelCat_all.append(fuelCat_)

        fuelCat_all = pd.concat(fuelCat_all)
        print(' done')

    else: 
    #elif continent == 'asia':
        indir = '{:s}CLC/'.format(dir_data)
        to_latlon = pyproj.Transformer.from_crs(crs_here, 'epsg:4326')
        lowerCorner = to_latlon.transform(xminAll, yminAll)
        upperCorner = to_latlon.transform(xmaxAll, ymaxAll)
        fuelCat_all = None
        for iv in idxclc:  
            print(iv)
            if fuelCat_all is None:
                fuelCat_all = glc.clipped_fuelCat_raster(indir, iv, crs_here, xminAll, yminAll, xmaxAll, ymaxAll ) 
                fuelCat_all.data[fuelCat_all.mask == False] = iv
                #fuelCat_all['ICat'] = iv
            else:
                fuelCat_ = glc.clipped_fuelCat_raster(indir, iv, crs_here, xminAll, yminAll, xmaxAll, ymaxAll) 
                #fuelCat_['ICat'] = iv
                fuelCat_all.data[fuelCat_.mask == False] = iv
                fuelCat_all.mask[fuelCat_.mask == False] = False
                fuelCat_ = None

    return idxclc, fuelCat_all



if __name__ == '__main__':
    
    #continent = 'asia'
    continent = 'namerica'
    
    importlib.reload(tools)
    importlib.reload(glc)
  
    dir_data = tools.get_dirData()

    '''
    if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
    elif continent == 'asia':
        xminAll,xmaxAll = -1.315e7, -6.e4
        yminAll,ymaxAll = -1.79e6, 7.93e6
        #xminAll,xmaxAll = -3.35e6,  -1.26e6
        #yminAll,ymaxAll = 3.32e6,  4.79e6
        #crs_here = 'epsg:3832'
        crs_here = 'epsg:8859'
    '''
    params = params.load_param(continent)
    xminAll,xmaxAll = params['xminAll'], params['xmaxAll']
    yminAll,ymaxAll = params['yminAll'], params['ymaxAll']
    crs_here        = params['crs_here']
    bufferBorder    = params['bufferBorder']


    #borders
    indir = '{:s}Boundaries/'.format(dir_data)
    if continent == 'europe':
        bordersNUTS = gpd.read_file(indir+'NUTS/NUTS_RG_01M_2021_4326.geojson')
        bordersNUST = bordersNUTS.to_crs(crs_here)
        extraNUTS = gpd.read_file(indir+'noNUTS.geojson')
        extraNUST = extraNUTS.to_crs(crs_here)
        bordersSelection = pd.concat([bordersNUST,extraNUST])
    elif (continent == 'asia') | (continent == 'namerica'): 
        bordersSelection = gpd.read_file(indir+'mask_{:s}.geojson'.format(continent))
        bordersSelection = bordersSelection[['SOV_A3', 'geometry', 'LEVL_CODE']]
        bordersSelection = bordersSelection.dissolve(by='SOV_A3', aggfunc='sum').reset_index()
    bordersSelection = bordersSelection.to_crs(crs_here)
        
    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    landNE = landNE.to_crs(crs_here)

    #load graticule
    gratreso = 15
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))
    graticule = graticule.to_crs(crs_here)


    dirout = '{:s}Maps-Product/{:s}/'.format(dir_data,continent)
    
    colorCat=['darkgreen', 'fuchsia', 'gold', 'tomato' ,'teal']
    color_dict = {'vegetation category 1':colorCat[0], 
                  'vegetation category 2':colorCat[1],
                  'vegetation category 3':colorCat[2],
                  'vegetation category 4':colorCat[3],
                  'vegetation category 5':colorCat[4], }
    
    idxclc, fuelCat_all = loadFuelCat(continent, crs_here, xminAll, yminAll, xmaxAll, ymaxAll)
           
        #map to crs_here

    #plot
    
    mpl.rcdefaults()
    #mpl.rcParams['legend.fontsize'] = 8

    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    if type(fuelCat_all) is gpd.geodataframe.GeoDataFrame:
        fuelCat_all.plot(ax=ax, column='rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())),zorder=4)
    else: 
        im = ax.imshow(fuelCat_all, cmap=colors.ListedColormap(list(color_dict.values())),extent=(xminAll,xmaxAll,yminAll, ymaxAll),interpolation='nearest', zorder=4)
        #legend=ep.draw_legend(
        #    im,
        #    titles=["vegetation category 1", "vegetation category 2", "vegetation category 3", "vegetation category 4", "vegetation category 5"],
        #    classes=[1, 2, 3, 4, 5],
        #)
        patches = [mpl.patches.Patch(color=color, label=label) for label, color in color_dict.items() ]
        ax.legend(handles=patches, bbox_to_anchor=(.45, .24), facecolor="white", prop={'size':10})

        landNE_outside = gpd.overlay(landNE, bordersSelection[bordersSelection['LEVL_CODE']==0], how = 'difference')
        landNE_outside.buffer(1.e4).plot(ax=ax, facecolor='0.9', edgecolor='None',zorder=5)

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

    ax.set_title('Fuel Categories Area', pad=30)
   
    fig.savefig(dirout+'FuelCatArea_CLC.png',dpi=200)
    plt.close(fig)
