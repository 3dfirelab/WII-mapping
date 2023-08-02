import sys
import os 
import pandas as pd
import geopandas as gpd
import shapely 
import glob
import matplotlib as mpl 
from matplotlib import pyplot as plt
import matplotlib.colors as colors
from shapely.geometry import Polygon
import importlib
import warnings
import pdb 
import pyproj
from fiona.crs import from_epsg
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
import rasterio 
from rasterio.mask import mask
import numpy as np 

#homebrewed
sys.path.append('../src-map/')
import tools
import mapFuelCat
glc = importlib.import_module("load-glc-category")
import params 


warnings.filterwarnings("ignore")

if __name__ == '__main__':

    dir_data = tools.get_dirData()
    continent = 'europe'
    flag_onlyplot = True

    #importlib.reload(tools)
    params = params.load_param(continent)
    xminAll,xmaxAll = params['xminAll'], params['xmaxAll']
    yminAll,ymaxAll = params['yminAll'], params['ymaxAll']
    crs_here        = params['crs_here']
    bufferBorder    = params['bufferBorder']
    lonlat_bounds   = params['lonlat_bounds']
    gratreso        = params['gratreso']

    if continent == 'europe':
        #cataluna
        #xminHere,xmaxHere = 3.6370e6, 3.6760e6 
        #yminHere,ymaxHere = 2.0805e6, 2.1159e6 
        #filein = '{:s}/TrueColor/2023-03-03-00 00_2023-03-03-23 59_Sentinel-2_L2A_True_color.tiff'.format(dir_data)
        xminHere,xmaxHere = 4.215450e6, 4.249948e6 
        yminHere,ymaxHere = 1.755465e6, 1.802953e6 
        filein = None 
 
    else: 
        print('working for europe')
        sys.exit()
  
    to_latlon=pyproj.Transformer.from_crs(crs_here, 'epsg:4326')
    xmean = .5*(xminHere+xmaxHere)
    ymean = .5*(yminHere+ymaxHere)
    print(to_latlon.transform(ymean,xmean))

    if filein is not None:
        #get true color image
        with rasterio.open(filein) as src:
            
            #clip
            bb = 2000
            bbox = shapely.geometry.box(xminHere-bb, yminHere-bb, xmaxHere+bb, ymaxHere+bb)
            geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=crs_here)
            geo = geo.to_crs(crs='epsg:4326')
            coords = glc.getFeatures(geo)
            data_, src_transform = mask(src, shapes=coords, crop=True)
           
            data_out = []
            for xx in range(3):
                band_, transform_dst = tools.reproject_raster(data_[xx][np.newaxis, ...], geo.total_bounds , src_transform, geo.crs, crs_here, resolution=60)
                
                if xx == 0: 
                    transformer = rasterio.transform.AffineTransformer(transform_dst)
                    nx,ny = band_.shape
                    dst_bounds = (*transformer.xy(0, 0), *transformer.xy(nx, ny))

                data_out.append(band_)

        data_out = np.array(data_out, dtype=np.uint8)
        data_out = np.transpose(data_out,[1,2,0])
        norm = (data_out * (255 / np.max(data_out))).astype(np.uint8)
    else:
        norm = None

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
   
    #if continent == 'russia':
    #    bordersSelection['geometry'] = bordersSelection.buffer(.5).buffer(-.5) # pb at 180 to -180. close small gap

    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    #load graticule
    #gratreso = 5
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))

    if lonlat_bounds is not None:
        landNE_ = pd.concat( [ gpd.clip(landNE,lonlat_bounds_) for lonlat_bounds_ in lonlat_bounds])
        graticule_ = pd.concat( [ gpd.clip(graticule,lonlat_bounds_) for lonlat_bounds_ in lonlat_bounds])
    else: 
        landNE_ = landNE
        graticule_= graticule

    landNE = landNE_.to_crs(crs_here)
    graticule = graticule_.to_crs(crs_here)

    '''
    #borders
    indir = '/mnt/dataEuropa/WII/Boundaries/'
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

    #load graticule
    gratreso = 15
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))
    graticule = graticule.to_crs(crs_here)
    '''

    #industrial zone
    indir = '{:s}/Maps-Product/{:s}/'.format(dir_data, continent)
    indusAll = gpd.read_file(indir+'industrialZone_osmSource.geojson')
    
    #WII
    indir = '{:s}/Maps-Product/{:s}/'.format(dir_data, continent)
    WIIAll = gpd.read_file(indir+'WII-unary_union.geojson')
   
    #Fuel
    idxclc, fuelCat_all = mapFuelCat.loadFuelCat(dir_data, continent, crs_here, xminAll, yminAll, xmaxAll, ymaxAll, bordersSelection)
    
    #add hazard
    if continent == 'europe':
        fuelCat_all['IAI'] = -999
        fuelCat_all.loc[(fuelCat_all['AI']>0.9)                         ,'IAI'] = 0
        fuelCat_all.loc[(fuelCat_all['AI']>0  )&(fuelCat_all['AI']<=0.9),'IAI'] = 1
        fuelCat_all.loc[(fuelCat_all['AI']<=0 )                         ,'IAI'] = 2 # to update to pass it to ==0. need PoverA update. 

        fuelCat_all['IFH'] = fuelCat_all['ICat'] + fuelCat_all['IAI']
        fuelCat_all['FH_rank'] = 'hazard category ' + fuelCat_all['IFH'].astype(str)
    else: 
        print('****** no fire hazard rank available here for continent = '.format(continent))
        sys.exit()

    dirout = '{:s}/Maps-Product/{:s}/'.format(dir_data,continent)


    #plot geo
    ####
    '''
    mpl.rcdefaults()
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    bbox = shapely.geometry.box(xminHere, yminHere, xmaxHere, ymaxHere)
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(crs_here.split(':')[1]))
    geo['geometry'] = geo.boundary
    geo.plot(ax=ax,edgecolor='k',zorder=2,linewidth=0.5)

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

    ax.set_title('ZoomLocation', pad=10)
    
    fig.savefig(dirout+'ZoomLocation.png',dpi=200)
    plt.close(fig)
    '''

    #plot 4
    ####
    mpl.rcdefaults()
    mpl.rcParams['figure.subplot.left'] = .05
    mpl.rcParams['figure.subplot.right'] = .95
    mpl.rcParams['figure.subplot.top'] = 0.95
    mpl.rcParams['figure.subplot.bottom'] = .05
    mpl.rcParams['figure.subplot.hspace'] = 0.05
    mpl.rcParams['figure.subplot.wspace'] = 0.05
    fig = plt.figure(figsize=(10,10))

    ax = plt.subplot(221)
    #landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    #graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    #bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)
    if norm is not None: 
        ax.imshow(norm, extent=(dst_bounds[0],dst_bounds[2],dst_bounds[3],dst_bounds[1]), alpha=0.89)

    indusAll.cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2,zorder=4)
    
    ax.set_xlim(xminHere,xmaxHere)
    ax.set_ylim(yminHere,ymaxHere)
    ax.set_title('Industrial Area + sentinel2 true color image (60m)', pad=10)
    ax.set_axis_off()

    fontprops = fm.FontProperties(size=10)
    scalebar = AnchoredSizeBar(ax.transData,
                               3000, '3 km', 'upper right', 
                               pad=.3,
                               color='k',
                               frameon=True,
                               size_vertical=10,
                               fontproperties=fontprops)

    ax.add_artist(scalebar)

    ax = plt.subplot(222)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)
    
    colorCat=['darkgreen', 'fuchsia', 'gold', 'tomato' ,'teal']
    color_dict = {'vegetation category 1':colorCat[0], 
                  'vegetation category 2':colorCat[1],
                  'vegetation category 3':colorCat[2],
                  'vegetation category 4':colorCat[3],
                  'vegetation category 5':colorCat[4], }

    fuelCat_all.cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, column='rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())),zorder=4)
    indusAll.cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2,zorder=5, )
    
    ax.set_xlim(xminHere,xmaxHere)
    ax.set_ylim(yminHere,ymaxHere)
    ax.set_title('Fuel Categories Area', pad=10)
    ax.set_axis_off()


    ax = plt.subplot(223)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)
    
    colorCat=['tab:red', 'tab:orange', 'tab:pink', 'tab:purple' ,'tab:brown', 'tab:cyan' ,'tab:blue']
    color_dict = {'hazard category 1':colorCat[0], 
                  'hazard category 2':colorCat[1],
                  'hazard category 3':colorCat[2],
                  'hazard category 4':colorCat[3],
                  'hazard category 5':colorCat[4],
                  'hazard category 6':colorCat[5],
                  'hazard category 7':colorCat[6], }
    
    hatches = ['///////', '', '+++', '', '', '', 'oooo']
    edgecolors = list(color_dict.values())
    facecolors = ['w', edgecolors[1], 'w', edgecolors[3], 'w', 'w', 'w']

    polys = []
    labels = []
    for ic in np.arange(1,8):
        fuelcati_ = fuelCat_all[(fuelCat_all['FH_rank'] == list(color_dict.keys())[ic-1])].cx[xminHere:xmaxHere, yminHere:ymaxHere]
        if fuelcati_.shape[0]>0:
            fuelcati_.plot(ax=ax,facecolor=facecolors[ic-1], hatch=hatches[ic-1], edgecolor=edgecolors[ic-1], linewidth=0.2, zorder=4) 
            labels.append( list(color_dict.keys())[ic-1] )
            polys.append( mpl.patches.Polygon(np.random.rand(3 ,2), facecolor=facecolors[ic-1], edgecolor=edgecolors[ic-1], linewidth=0.2, hatch=hatches[ic-1]) )
    ax.legend(polys, labels, )

    #fuelCat_all[fuelCat_all['FH_rank']==1].cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, column='FH_rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())),hatch='\\', zorder=4)
    #fuelCat_all[fuelCat_all['FH_rank']==2].cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, column='FH_rank', legend=True, cmap=colors.ListedColormap(list(color_dict.values())), zorder=4)
    indusAll.cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2,zorder=5,)
    
    ax.set_xlim(xminHere,xmaxHere)
    ax.set_ylim(yminHere,ymaxHere)
    ax.set_title('Fire Hazard Categories Area', pad=10)
    ax.set_axis_off()


    ax = plt.subplot(224)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
    bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

    WIIAll.cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, facecolor='hotpink', edgecolor='hotpink', linewidth=.2,zorder=4)
    indusAll.cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2,zorder=5, )
    
    ax.set_xlim(xminHere,xmaxHere)
    ax.set_ylim(yminHere,ymaxHere)
    ax.set_title('Wildland Industrial Interface', pad=10)
    ax.set_axis_off()


    plt.show()

    #fig.savefig(dirout+'ZoomIndusFuelHazardWII.png',dpi=200)
    #plt.close(fig)


    '''    #print('fueltCat{:d}'.format(iv))
        key = 'fuelCat{:d}_dist'.format(iv)
        key2 = 'fuelCat{:d}_idx'.format(iv)
        indus[key], indus[key2] = tools.dist2FuelCat(indir, fuelCat_all[iv-1], indus)

    indus.to_file(dirout+'_dist.'.join(os.path.basename(indusFile).split('.')), driver="GeoJSON")
    '''

    #sys.exit()

    '''
    ax = plt.subplot(111)
    bdf.plot(color='white', edgecolor='black',ax=ax, linewidth=0.2)
    indus.plot(column=indus[key],ax=ax)
    
    minx, miny, maxx, maxy = indus.total_bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    plt.show()
    '''
