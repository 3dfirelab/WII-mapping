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
from fiona.crs import from_epsg
import pdb 

#homebrewed
import tools
import params

if __name__ == '__main__':
    
    continent = 'samerica'
    dir_data = tools.get_dirData()

    importlib.reload(tools)
    
    '''
    if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
        bufferBorder = -1800
    elif continent == 'asia':
        xminAll,xmaxAll = -1.315e7, -6.e4
        yminAll,ymaxAll = -1.79e6, 7.93e6
        crs_here = 'epsg:8859'
        bufferBorder = -10000
    '''
    params = params.load_param(continent)
    xminAll,xmaxAll = params['xminAll'], params['xmaxAll']
    yminAll,ymaxAll = params['yminAll'], params['ymaxAll']
    crs_here        = params['crs_here']
    bufferBorder    = params['bufferBorder']
    lonlat_bounds   = params['lonlat_bounds']

    #borders
    indir = '{:s}Boundaries/'.format(dir_data)
    if continent == 'europe':
        bordersNUTS = gpd.read_file(indir+'NUTS/NUTS_RG_01M_2021_4326.geojson')
        bordersNUST = bordersNUTS.to_crs(crs_here)
        extraNUTS = gpd.read_file(indir+'noNUTS.geojson')
        extraNUST = extraNUTS.to_crs(crs_here)
        bordersSelection = pd.concat([bordersNUST,extraNUST])
    else:
        bordersSelection = tools.my_read_file(indir+'mask_{:s}.geojson'.format(continent))
        bordersSelection = bordersSelection[['SOV_A3', 'geometry', 'LEVL_CODE']]
        bordersSelection = bordersSelection.dissolve(by='SOV_A3', aggfunc='sum').reset_index()
    bordersSelection = bordersSelection.to_crs(crs_here)

    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    if lonlat_bounds is not None:
        landNE_ = pd.concat( [ gpd.clip(landNE,lonlat_bounds) for lonlat_bounds_ in lonlat_bounds])
    else: 
        landNE_ = landNE
    landNE = landNE_.to_crs(crs_here)
 
    #load graticule
    gratreso = 15
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))
    graticule = graticule.to_crs(crs_here)

    #industrial zon
    indir = '{:s}IndustrialZone/{:s}/'.format(dir_data,continent)
    indusFiles = sorted(glob.glob(indir+'*.geojson'))

    dirout = '{:s}Maps-Product/{:s}/'.format(dir_data,continent)
    
    if not(os.path.isfile(dirout+'industrialZone_osmSource.geojson')):
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

        indusAll.to_file(dirout+'industrialZone_osmSource.geojson',driver='GeoJSON')
        if indusAll.crs.to_epsg() is None: 
            with open(dirout+'industrialZone_osmSource.prj','w') as f:
                f.write(indusAll.crs.to_wkt())
        '''
        need to find a trick to save crs for namerica as it is not an epsg code
        saving in geojson reset it to lalon WGS84
        '''
    else: 
        indusAll = tools.my_read_file(dirout+'industrialZone_osmSource.geojson')

    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    bordersSelection.buffer(bufferBorder)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    indusAll.plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2,zorder=4)
    ax.set_xlim(xminAll,xmaxAll)
    ax.set_ylim(yminAll,ymaxAll)
    
    #set axis
    bbox = shapely.geometry.box(xminAll, yminAll, xmaxAll, ymaxAll)
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=indusAll.crs)
    geo['geometry'] = geo.boundary
    ptsEdge =  gpd.overlay(graticule, geo, how = 'intersection', keep_geom_type=False)
    
    lline = shapely.geometry.LineString([[xminAll,ymaxAll],[xmaxAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=indusAll.crs)
    ptsEdgelon =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
    
    ax.xaxis.set_ticks(ptsEdgelon.geometry.centroid.x)
    ax.xaxis.set_ticklabels(ptsEdgelon.display, rotation=33)
    ax.xaxis.tick_top()
    
    lline = shapely.geometry.LineString([[xminAll,yminAll],[xminAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=indusAll.crs)
    ptsEdgelat =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)

    ax.yaxis.set_ticks(ptsEdgelat.geometry.centroid.y)
    ax.yaxis.set_ticklabels(ptsEdgelat.display)


    ax.set_title('Industrial Area', pad=30)
    fig.savefig(dirout+'industrialArea_OSM.png',dpi=200)
    plt.close(fig)
