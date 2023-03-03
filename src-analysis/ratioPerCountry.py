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

if __name__ == '__main__':

    continent = 'europe'

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
        bordersSelection = pd.concat([bordersNUST,extraNUST],ignore_index=True)
    elif continent == 'asia':
        bordersSelection = gpd.read_file(indir+'mask_{:s}.geojson'.format(continent))

    bordersSelection = bordersSelection.reset_index()

    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    landNE = landNE.to_crs(crs_here)


    #industrial zone
    indir = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
    indus = gpd.read_file(indir+'industrialZone_osmSource.geojon')
    WII = gpd.read_file(indir+'WII.geojon')

    dirout = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
     
    #per country
    ############
    selection = bordersSelection[bordersSelection['LEVL_CODE']==0].reset_index()
    selection['WIIoverIndus'] = -999
    for ipoly in range(len(selection)):
        indus_ = gpd.overlay(selection[ipoly:ipoly+1], indus, how = 'intersection', keep_geom_type=False)
        WII_ = gpd.overlay(selection[ipoly:ipoly+1], WII, how = 'intersection', keep_geom_type=False)
        selection.loc[ipoly,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum()
    #plot
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')
    bordersSelection.buffer(-1.e4)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None')

    selection.plot(ax=ax,cax=cax,column='WIIoverIndus',legend=True,vmax=np.percentile(selection['WIIoverIndus'],95))
    ax.set_xlim(xminEU,xmaxEU)
    ax.set_ylim(yminEU,ymaxEU)
    ax.set_title('Ratio WII Area over Industrial Area per Country')
    fig.savefig(dirout+'RatioWIIoverIndus.png',dpi=200)
    plt.close(fig)


    #per province
    ############
    if continent=='europe':
        selectionProv = bordersNUST[bordersNUST['LEVL_CODE']==3].reset_index()
        selectionProv['WIIoverIndus'] = -999
        selectionProv['IndusAera'] = -999
        selectionProv['WIIAera'] = -999
        for ipoly in range(len(selectionProv)):
            indus_ = gpd.overlay(selectionProv[ipoly:ipoly+1], indus, how = 'intersection', keep_geom_type=False)
            WII_ = gpd.overlay(selectionProv[ipoly:ipoly+1], WII, how = 'intersection', keep_geom_type=False)
            selectionProv.loc[ipoly,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum()
            selectionProv.loc[ipoly,'WIIAera_ha'] = WII_.area.sum()*1.e-4
            selectionProv.loc[ipoly,'IndusAera_ha'] = indus_.area.sum()*1.e-4

        pd.DataFrame(gdf.drop(columns='geometry')).to_csv(dirout+'{:s}_info_province'.format(continent))
        #plot
        fig = plt.figure(figsize=(10,8))
        ax = plt.subplot(111)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        landNE.plot(ax=ax,facecolor='0.9',edgecolor='None')

        selectionProv.plot(ax=ax,cax=cax,column='WIIoverIndus',legend=True,vmax=np.percentile(selection['WIIoverIndus'],95))
        ax.set_xlim(xminEU,xmaxEU)
        ax.set_ylim(yminEU,ymaxEU)
        ax.set_title('Ratio WII Area over Industrial Area per Province in the European Union')
        fig.savefig(dirout+'RatioWIIoverIndus_province.png',dpi=200)
        plt.close(fig)


