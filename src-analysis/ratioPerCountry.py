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
import rasterio
from rasterio.mask import mask

sys.path.append('../src-map/')
import mapFuelCat
import tools 
import params

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

def fuelCatAreaFromraster(indir, geoMask):

    #print('fuel global lc')
    fuelCatTag = []
    fuelCatTag.append([111,113,121,123]) #1
    fuelCatTag.append([115,116,125,126]) #2
    fuelCatTag.append([112,114,122,124,20,30]) #3
    fuelCatTag.append([90]) #4
    fuelCatTag.append([100]) #5

    filein = indir + 'PROBAV_LC100_global_v3.0.1_2018-conso_Discrete-Classification-map_EPSG-4326.tif'
    crs_here = geoMask.crs 

    rasterlc = []
    reso = 1.e2
    with rasterio.open(filein) as src:

        #clip
        geoMask = geoMask.to_crs('epsg:4326')
        coords = getFeatures(geoMask)
        rasterlc, src_transform = mask(src, shapes=coords, crop=True)
        
        transformer = rasterio.transform.AffineTransformer(src_transform)
        _, nx,ny = rasterlc.shape
        src_bounds = (*transformer.xy(0, 0), *transformer.xy(nx, ny))

        rasterlc_m, transform_out = tools.reproject_raster(rasterlc, src_bounds, src_transform, src.crs, crs_here, resolution =reso)

        #gt = src.tansform
        dx =    transform_out[0] 
        dy = -1*transform_out[4]  

    totalArea = 0
    data_out = []
    for iv in range(1,6):
        condition = (rasterlc_m==fuelCatTag[iv-1][0])
        if len(fuelCatTag[iv-1]) > 1:
            for xx in fuelCatTag[iv-1][1:]:
                condition |= (rasterlc_m==xx)
        data_out_masked = np.ma.masked_where(np.invert(condition), rasterlc_m)
        
        print(np.where(data_out_masked.mask==False)[0].shape[0] * dx*dy)
        totalArea += np.where(data_out_masked.mask==False)[0].shape[0] * dx*dy
        data_out.append(data_out_masked)
    
    print('---')
    return  1.e-4*totalArea, data_out




if __name__ == '__main__':

    continent = 'asia'

   '''
   if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
    elif continent == 'asia':
        xminAll,xmaxAll = -1.315e7, -6.e4
        yminAll,ymaxAll = -1.79e6, 7.93e6
        crs_here = 'epsg:8859'
    '''
    params = params.load_param(continent)
    xminAll,xmaxAll = params['xminAll'], params['xmaxAll']
    yminAll,ymaxAll = params['yminAll'], params['ymaxAll']
    crs_here        = params['crs_here']
    bufferBorder    = params['bufferBorder']

 
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
        bordersSelection = bordersSelection.dissolve(by='SOV_A3', aggfunc='sum')

        #print('******')
        #print('need a conversion to polygon for fuelCat_all for asia')
        #print('or need to change totalAreaFuelCat caclulation below')
        #print('******')
        #sys.exit()

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
    #WII
    WII = gpd.read_file(indir+'WII.geojon')
    #FuelCat
    if continent == 'europe':
        idxclc, fuelCat_all = mapFuelCat.loadFuelCat(continent, crs_here, xminAll, yminAll, xmaxAll, ymaxAll)
    else: 
        fuelCat_all = None

    dirout = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
    
    #per country
    ############
    print('per country:')
    selection = bordersSelection[bordersSelection['LEVL_CODE']==0].reset_index()
    selection['WIIoverIndus'] = -999
    selection['WIIoverFuel'] = -999
    nn = len(selection)
    for ipoly in range(len(selection)):
        print('{:05.1f} %'.format(100*ipoly/nn), end='\r')
        sys.stdout.flush()
        sxmin, symin, sxmax, symax = selection[ipoly:ipoly+1].total_bounds
        
        tmp = indus.cx[sxmin:sxmax,symin:symax]
        indus_ = gpd.overlay(selection[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
        
        tmp = WII.cx[sxmin:sxmax,symin:symax]
        WII_ = gpd.overlay(selection[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
        
        if type(fuelCat_all) is gpd.GeoDataFrame :
            tmp = fuelCat_all.cx[sxmin:sxmax,symin:symax]
            fuelCat_all_ = gpd.overlay(selection[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
            totalAreaFuelCat = fuelCat_all_.area.sum()*1.e-4

        else:
            indir = '/mnt/dataEstrella/WII/CLC/'
            totalAreaFuelCat, fuelMap = fuelCatAreaFromraster(indir, selection[ipoly:ipoly+1]) 

        if totalAreaFuelCat > selection[ipoly:ipoly+1].area.sum()*1.e-4 : 
            pdb.set_trace()

        selection.loc[ipoly,'WIIAera_ha'] = WII_.area.sum()*1.e-4
        selection.loc[ipoly,'IndusAera_ha'] = indus_.area.sum()*1.e-4
        selection.loc[ipoly,'FuelCatAera_ha'] = totalAreaFuelCat
        selection.loc[ipoly,'CountrySize_ha'] = selection[ipoly:ipoly+1].area.sum()*1.e-4
        
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
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    #bordersSelection.buffer(-1.e4)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    selection.plot(ax=ax,cax=cax,column='WIIoverIndus',legend=True,vmax=np.percentile(selection['WIIoverIndus'],95),zorder=2)
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
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    #bordersSelection.buffer(-1.e4)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    mm = selection.dropna(subset=['WIIoverFuel'])
    mm.plot(ax=ax,cax=cax,column='WIIoverFuel',legend=True,vmax=np.percentile(mm['WIIoverFuel'],80),zorder=2)
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
    ax.set_title('Ratio WII Area over total Fuel Area per Country', pad=30)
    fig.savefig(dirout+'RatioWIIoverFuel.png',dpi=200)
    plt.close(fig)
    
    #save csv
    #########
    pd.DataFrame(selection.drop(columns='geometry')).to_csv(dirout+'{:s}_info_country.csv'.format(continent))

    #per province
    ############
    print('per province:')
    if continent=='europe':
        selectionProv = bordersNUST[bordersNUST['LEVL_CODE']==3].reset_index()
        selectionProv['WIIoverIndus'] = -999
        selectionProv['WIIoverFuel'] = -999
        selectionProv['IndusAera'] = -999
        selectionProv['WIIAera'] = -999
        nn = len(selectionProv)
        for ipoly in range(len(selectionProv)):
            print('{:05.1f} %'.format(100*ipoly/nn), end='\r')
            sxmin, symin, sxmax, symax = selectionProv[ipoly:ipoly+1].total_bounds
            
            tmp = indus.cx[sxmin:sxmax,symin:symax]
            indus_ =       gpd.overlay(selectionProv[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
        
            tmp = WII.cx[sxmin:sxmax,symin:symax]
            WII_         = gpd.overlay(selectionProv[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
            
            tmp = fuelCat_all.cx[sxmin:sxmax,symin:symax]
            fuelCat_all_ = gpd.overlay(selectionProv[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
        
            totalAreaFuelCat = fuelCat_all_.area.sum()*1.e-4

            selectionProv.loc[ipoly,'WIIAera_ha'] = WII_.area.sum()*1.e-4
            selectionProv.loc[ipoly,'IndusAera_ha'] = indus_.area.sum()*1.e-4
            selectionProv.loc[ipoly,'FuelCatAera_ha'] = totalAreaFuelCat
            
            selectionProv.loc[ipoly,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum()
            selectionProv.loc[ipoly,'WIIoverFuel']  = WII_.area.sum()/(totalAreaFuelCat*1.e4)


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

        ax.set_title('Ratio WII Area over Industrial Area per Province in the European Union', pad=30)
        fig.savefig(dirout+'RatioWIIoverIndus_province.png',dpi=200)
        plt.close(fig)

        
        #fuel
        fig = plt.figure(figsize=(10,8))
        ax = plt.subplot(111)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
        graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)

        selectionProv.plot(ax=ax,cax=cax,column='WIIoverFuel',legend=True,vmax=np.percentile(selection['WIIoverFuel'],95),zorder=2)
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

