import sys
import os 
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely 
import glob
from matplotlib import pyplot as plt
from shapely.geometry import Polygon
import importlib
import warnings
import pdb 
from mpl_toolkits.axes_grid1 import make_axes_locatable
warnings.filterwarnings("ignore")
import pyproj
from fiona.crs import from_epsg

sys.path.append('../src-map/')
import mapFuelCat

if __name__ == '__main__':

    continent = 'europe'

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
        bordersSelection = pd.concat([bordersNUST,extraNUST],ignore_index=True)
    elif continent == 'asia':
        bordersSelection = gpd.read_file(indir+'mask_{:s}.geojson'.format(continent))

        print('******')
        print('need a conversion to polygon for fuelCat_all for asia')
        print('or need to change totalAreaFuelCat caclulation below')
        print('******')
        sys.exit()

    bordersSelection = bordersSelection.reset_index()

    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    landNE = landNE.to_crs(crs_here)
    
    #load graticule
    gratreso = 15
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))
    graticule = graticule.to_crs(crs_here)

    #industrial zone
    indir = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
    indus = gpd.read_file(indir+'industrialZone_osmSource.geojon')
    #FuelCat
    idxclc, fuelCat_all = mapFuelCat.loadFuelCat(continent, crs_here, xminAll, yminAll, xmaxAll, ymaxAll)
    #WII
    WII = gpd.read_file(indir+'WII.geojon')

    dirout = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
    
    #per country
    ############
    selection = bordersSelection[bordersSelection['LEVL_CODE']==0].reset_index()
    selection['WIIoverIndus'] = -999
    selection['WIIoverFuel'] = -999
    for ipoly in range(len(selection)):
        indus_ = gpd.overlay(selection[ipoly:ipoly+1], indus, how = 'intersection', keep_geom_type=False)
        WII_ = gpd.overlay(selection[ipoly:ipoly+1], WII, how = 'intersection', keep_geom_type=False)
        fuelCat_all_ = gpd.overlay(selection[ipoly:ipoly+1], fuelCat_all, how = 'intersection', keep_geom_type=False)
        
        totalAreaFuelCat = fuelCat_all_.area.sum()*1.e-4

        selection.loc[ipoly,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum()
        selection.loc[ipoly,'WIIoverFuel']  = WII_.area.sum()/(totalAreaFuelCat*1.e4)

    #plot
    #####
    #indus
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=4)
    bordersSelection.buffer(-1.e4)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    selection.plot(ax=ax,cax=cax,column='WIIoverIndus',legend=True,vmax=np.percentile(selection['WIIoverIndus'],95),zorder=3)
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

    ax.set_title('Ratio WII Area over Industrial Area per Country', pad=30)
    fig.savefig(dirout+'RatioWIIoverIndus.png',dpi=200)
    plt.close(fig)

    #fuel
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')
    bordersSelection.buffer(-1.e4)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None')

    selection.plot(ax=ax,cax=cax,column='WIIoverFuel',legend=True,vmax=np.percentile(selection['WIIoverFuel'],95))
    ax.set_xlim(xminAll,xmaxAll)
    ax.set_ylim(yminAll,ymaxAll)
    ax.set_title('Ratio WII Area over total Fuel Area per Country', pad=30)
    fig.savefig(dirout+'RatioWIIoverFuel.png',dpi=200)
    plt.close(fig)

    #per province
    ############
    if continent=='europe':
        selectionProv = bordersNUST[bordersNUST['LEVL_CODE']==3].reset_index()
        selectionProv['WIIoverIndus'] = -999
        selectionProv['WIIoverFuel'] = -999
        selectionProv['IndusAera'] = -999
        selectionProv['WIIAera'] = -999
        for ipoly in range(len(selectionProv)):
            indus_       = gpd.overlay(selectionProv[ipoly:ipoly+1], indus, how = 'intersection', keep_geom_type=False)
            WII_         = gpd.overlay(selectionProv[ipoly:ipoly+1], WII, how = 'intersection', keep_geom_type=False)
            fuelCat_all_ = gpd.overlay(selectionProv[ipoly:ipoly+1], fuelCat_all, how = 'intersection', keep_geom_type=False)
        
            totalAreaFuelCat = fuelCat_all_.area.sum()*1.e-4

            selectionProv.loc[ipoly,'WIIAera_ha'] = WII_.area.sum()*1.e-4
            selectionProv.loc[ipoly,'IndusAera_ha'] = indus_.area.sum()*1.e-4
            selectionProv.loc[ipoly,'FuelCatAera_ha'] = totalAreaFuelCat
            
            selectionProv.loc[ipoly,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum()
            selectionProv.loc[ipoly,'WIIoverFuel']  = WII_.area.sum()/(totalAreaFuelCat*1.e4)


        pd.DataFrame(selectionProv.drop(columns='geometry')).to_csv(dirout+'{:s}_info_province'.format(continent))
        #plot
        #####
        #indus
        fig = plt.figure(figsize=(10,8))
        ax = plt.subplot(111)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
        graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)

        selectionProv.plot(ax=ax,cax=cax,column='WIIoverIndus',legend=True,vmax=np.percentile(selection['WIIoverIndus'],95),zorder=2)
        ax.set_xlim(xminAll,xmaxAll)
        ax.set_ylim(yminAll,ymaxAll)

        ax.set_title('Ratio WII Area over Industrial Area per Province in the European Union')
        fig.savefig(dirout+'RatioWIIoverIndus_province.png',dpi=200)
        plt.close(fig)

        
        #fuel
        fig = plt.figure(figsize=(10,8))
        ax = plt.subplot(111)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')

        selectionProv.plot(ax=ax,cax=cax,column='WIIoverFuel',legend=True,vmax=np.percentile(selection['WIIoverFuel'],95))
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
        
        ax.set_title('Ratio WII Area over total Fuel Area per Province in the European Union', pad=30)
        fig.savefig(dirout+'RatioWIIoverFuel_province.png',dpi=200)
        plt.close(fig)


        #save csv
        #########
        pd.DataFrame(selectionProv.drop(columns='geometry')).to_csv(dirout+'{:s}_info_province.csv'.format(continent))

