import matplotlib as mpl
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
import argparse
import json

sys.path.append('../src-map/')
import mapFuelCat
import tools 
import params


###########################
#https://snorfalorpagus.net/blog/2016/03/13/splitting-large-polygons-for-faster-intersections/
###########################
def fishnet(geometry, threshold): #, srcbounds):
    bounds = geometry.bounds
    #try:
    #    xmin = int(max([bounds['minx'].values[0],srcbounds[0]]) // threshold)
    #    xmax = int(min([bounds['maxx'].values[0],srcbounds[2]]) // threshold)
    #    ymin = int(max([bounds['miny'].values[0],srcbounds[1]]) // threshold)
    #    ymax = int(min([bounds['maxy'].values[0],srcbounds[3]]) // threshold)
    #except:
    #    pdb.set_trace()
    
    xmin = int(bounds['minx'] // threshold)
    xmax = int(bounds['maxx'] // threshold)
    ymin = int(bounds['miny'] // threshold)
    ymax = int(bounds['maxy'] // threshold)
    
    ncols = int(xmax - xmin + 1)
    nrows = int(ymax - ymin + 1)
    result = []
    for i in range(xmin, xmax+1):
        for j in range(ymin, ymax+1):
            b = shapely.geometry.box(i*threshold, j*threshold, (i+1)*threshold, (j+1)*threshold)
            g = geometry.intersection(b)
            if g.iloc[0].is_empty:
                continue
            result.append(g)
   
    if len(result) == 0 : pdb.set_trace()

    return result


###########################
def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [xx['geometry'] for xx in json.loads(gdf.to_json())['features'] ]


###########################
def fuelCatAreaFromraster(indir, geoMask, checkName, xminContinent,yminContinent, xmaxContinent,ymaxContinent):

    #print('fuel global lc')
    fuelCatTag = []
    fuelCatTag.append([111,113,121,123]) #1
    fuelCatTag.append([115,116,125,126]) #2
    fuelCatTag.append([112,114,122,124,20,30]) #3
    fuelCatTag.append([90]) #4
    fuelCatTag.append([100]) #5

    filein = indir + 'PROBAV_LC100_global_v3.0.1_2018-conso_Discrete-Classification-map_EPSG-4326.tif'
    crs_here = geoMask.crs 
    
    totalArea = np.zeros([5])

    #rasterlc = []
    reso = 1.e2
    #data_out = []
    

    with rasterio.open(filein) as src:
        
        threshold = 1000.e3
        tiles = fishnet(geoMask, threshold)#, src.bounds)
      
        for tile in tiles: 
            #clip
            tile = gpd.clip(tile, (xminContinent,yminContinent, xmaxContinent,ymaxContinent)).explode().buffer(-.01).to_crs('epsg:4326').reset_index().drop(['level_0','level_1'], axis=1)
            tile = gpd.clip(tile, src.bounds)#for region above 80 lat

            if len(tile) == 0: 
                continue
            
            try:
                coords = getFeatures(tile)
            except: 
                pdb.set_trace()
          
            try: 
                rasterlc, src_transform = mask(src, shapes=coords, crop=True)
            except: 
                pdb.set_trace()

            transformer = rasterio.transform.AffineTransformer(src_transform)
            _, nx,ny = rasterlc.shape
            src_bounds = (*transformer.xy(0, 0), *transformer.xy(nx, ny))

            try:
                rasterlc_m, transform_out = tools.reproject_raster(rasterlc, src_bounds, src_transform, src.crs, crs_here, resolution =reso)
            except: 
                pdb.set_trace()
            #gt = src.tansform
            dx =    transform_out[0] 
            dy = -1*transform_out[4]  

            for iv in range(1,6):
                condition = (rasterlc_m==fuelCatTag[iv-1][0])
                if len(fuelCatTag[iv-1]) > 1:
                    for xx in fuelCatTag[iv-1][1:]:
                        condition |= (rasterlc_m==xx)
                data_out_masked = np.ma.masked_where(np.invert(condition), rasterlc_m)
                
                #print(np.where(data_out_masked.mask==False)[0].shape[0] * dx*dy)
                totalArea[iv-1] += np.where(data_out_masked.mask==False)[0].shape[0] * dx*dy
                #data_out.append(data_out_masked)

    #if totalArea.sum() == 0 : pdb.set_trace()
    #if checkName == 'Malaita': pdb.set_trace()

    #print('---')
    return  1.e-4*totalArea #, data_out



################################
if __name__ == '__main__':
################################


    parser = argparse.ArgumentParser(description='map WII')
    parser.add_argument('-c','--continent', help='continent name',required=True)
    args = parser.parse_args()
    
    continent = args.continent
    #continent = 'asia'

    dir_data = tools.get_dirData()
    
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
    distgroup       = params['distgroup']
    lonlat_bounds = params['lonlat_bounds']
    gratreso        = params['gratreso']
 
    #borders
    indir = '{:s}/Boundaries/'.format(dir_data)
    if continent == 'europe':
        bordersNUTS = gpd.read_file(indir+'NUTS/NUTS_RG_01M_2021_4326.geojson')
        bordersNUST = bordersNUTS.to_crs(crs_here)
        extraNUTS = gpd.read_file(indir+'noNUTS.geojson')
        extraNUST = extraNUTS.to_crs(crs_here)
        bordersSelection = pd.concat([bordersNUST,extraNUST],ignore_index=True)
    else: 
        #bordersSelection = gpd.read_file(indir+'mask_{:s}.geojson'.format(continent))
        #bordersSelection = bordersSelection.dissolve(by='SOV_A3', aggfunc='sum')
        bordersSelection = tools.my_read_file(indir+'mask_{:s}.geojson'.format(continent))
        bordersSelection = bordersSelection[['SOV_A3', 'geometry', 'LEVL_CODE', 'NAME']]
        bordersSelection = bordersSelection.dissolve(by='NAME', aggfunc='sum').reset_index()
        #print('******')
        #print('need a conversion to polygon for fuelCat_all for asia')
        #print('or need to change totalAreaFuelCat caclulation below')
        #print('******')
        #sys.exit()

    bordersSelection = bordersSelection.to_crs(crs_here)
    
    landNE = gpd.read_file(indir+'NaturalEarth_10m_physical/ne_10m_land.shp')
    #load graticule
    #gratreso = 15
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))

    if lonlat_bounds is not None:
        landNE_ = pd.concat( [ gpd.clip(landNE,lonlat_bounds_) for lonlat_bounds_ in lonlat_bounds])
        graticule_ = pd.concat( [ gpd.clip(graticule,lonlat_bounds_) for lonlat_bounds_ in lonlat_bounds])
    else: 
        landNE_ = landNE
        graticule_= graticule

    landNE = landNE_.to_crs(crs_here)
    graticule = graticule_.to_crs(crs_here)

    if continent == 'europe':
        provinces = bordersNUST[bordersNUST['LEVL_CODE']==3].reset_index()
        provincesAll = gpd.read_file(indir+'NaturalEarth_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp')
    else:
        provinces = gpd.read_file(indir+'NaturalEarth_10m_admin_1_states_provinces/ne_10m_admin_1_states_provinces.shp')

    if lonlat_bounds is not None:
        #bounds_ = np.array(lonlat_bounds)
        #provinces = provinces.cx[bounds_.min(axis=0)[0]:bounds_.min(axis=0)[2],bounds_.min(axis=0)[1]:bounds_.min(axis=0)[3]]
        provinces_ = pd.concat( [ gpd.clip(provinces,lonlat_bounds_) for lonlat_bounds_ in lonlat_bounds])
        if continent == 'europe':
            provincesAll_ = pd.concat( [ gpd.clip(provincesAll,lonlat_bounds_) for lonlat_bounds_ in lonlat_bounds])
        
    else:
        provinces_ = provinces
        if continent == 'europe':
            provincesAll_ = provincesAll
    
    provinces = provinces_.to_crs(crs_here)
    if continent == 'europe':
        provincesAll = provincesAll_.to_crs(crs_here)

    dirout = '{:s}/Maps-Product/{:s}/'.format(dir_data,continent)

    if os.path.isfile( dirout+'{:s}_info_province.geojson'.format(continent) ):
        outgdf = gpd.read_file(dirout+'{:s}_info_province.geojson'.format(continent))
        outgdf = outgdf.to_crs(crs_here)

    else:
        #industrial zone
        indir = '{:s}/Maps-Product/{:s}/'.format(dir_data,continent)
        indus = tools.my_read_file(indir+'industrialZone_osmSource.geojson')
        
        #WII
        try: 
            WII = tools.my_read_file(indir+'WII-unary_union.geojson')
        except: 
            print('need to run globAll.py before runing the ratio computation')
        
        #FuelCat
        if continent == 'europe':
            idxclc, fuelCat_all = mapFuelCat.loadFuelCat(dir_data, continent, crs_here, xminAll, yminAll, xmaxAll, ymaxAll,bordersSelection)
        else: 
            fuelCat_all = None

       
        '''
        if False:
            #per country
            ############
            print('per country:')
            selection = bordersSelection[bordersSelection['LEVL_CODE']==0].reset_index()
            selection['WIIoverIndus'] = -999
            selection['WIIoverFuel'] = -999
            if continent == 'europe': selection = selection.rename(columns={'NAME_LATN':'NAME'})
            
            nn = len(selection)
            selection = gpd.clip( selection, (xminAll, yminAll, xmaxAll, ymaxAll))
            
            for ipoly in range(len(selection)):
                print('{:05.1f} % -- {:s}'.format(100*ipoly/nn, selection.loc[ipoly,'NAME']), end='\r')
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
                    indir = '{:s}/CLC/'.format(dir_data)
                    totalAreaFuelCat = fuelCatAreaFromraster(indir, selection[ipoly:ipoly+1], selection.loc[ipoly,'NAME'], xminAll,yminAll, xmaxAll,ymaxAll) 

                if totalAreaFuelCat.sum() > selection[ipoly:ipoly+1].area.sum() : 
                    pdb.set_trace()

                selection.loc[ipoly,'WIIAera_ha'] = WII_.area.sum()*1.e-4
                selection.loc[ipoly,'IndusAera_ha'] = indus_.area.sum()*1.e-4
                selection.loc[ipoly,'FuelCatAera_ha'] = totalAreaFuelCat.sum()
                selection.loc[ipoly,'CountrySize_ha'] = selection[ipoly:ipoly+1].area.sum()*1.e-4
                
                selection.loc[ipoly,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum()
                selection.loc[ipoly,'WIIoverFuel']  = WII_.area.sum()/(totalAreaFuelCat.sum()*1.e4)

                selection.loc[ipoly,'FuelCatAera1_ha'] = totalAreaFuelCat[0]
                selection.loc[ipoly,'FuelCatAera2_ha'] = totalAreaFuelCat[1]
                selection.loc[ipoly,'FuelCatAera3_ha'] = totalAreaFuelCat[2]
                selection.loc[ipoly,'FuelCatAera4_ha'] = totalAreaFuelCat[3]
                selection.loc[ipoly,'FuelCatAera5_ha'] = totalAreaFuelCat[4]

            #plot
            #####
            mpl.rcdefaults()
            mpl.rcParams['font.size'] = 14
            mpl.rcParams['xtick.labelsize'] = 14
            mpl.rcParams['ytick.labelsize'] = 14
            mpl.rcParams['figure.subplot.left'] = .1
            mpl.rcParams['figure.subplot.right'] = .95
            mpl.rcParams['figure.subplot.top'] = .9
            mpl.rcParams['figure.subplot.bottom'] = .05

            #indus
            fig = plt.figure(figsize=(10,8))
            ax = plt.subplot(111)
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.1)
            landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
            graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
            #bordersSelection.buffer(-1.e4)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

            tmp_= np.where(selection['WIIoverIndus'])
            selection.plot(ax=ax,cax=cax,column='WIIoverIndus',legend=True,cmap=mpl.colors.LogNorm(vmin=tmp[np.where(tmp_>0)].min(),vmax=np.percentile(tmp_,95)),zorder=2)
            ax.set_xlim(xminAll,xmaxAll)
            ax.set_ylim(yminAll,ymaxAll)
            #set axis
            bbox = shapely.geometry.box(xminAll, yminAll, xmaxAll, ymaxAll)
            geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=WII.crs) #from_epsg(crs_here.split(':')[1]))
            geo['geometry'] = geo.boundary
            ptsEdge =  gpd.overlay(graticule, geo, how = 'intersection', keep_geom_type=False)
            
            lline = shapely.geometry.LineString([[xminAll,ymaxAll],[xmaxAll,ymaxAll]])
            geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=WII.crs) #from_epsg(crs_here.split(':')[1]))
            ptsEdgelon =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
            ptsEdgelon = ptsEdgelon[(ptsEdgelon['direction']!='N')&(ptsEdgelon['direction']!='S')]
            
            ax.xaxis.set_ticks(ptsEdgelon.geometry.centroid.x)
            ax.xaxis.set_ticklabels(ptsEdgelon.display)
            ax.xaxis.tick_top()
            
            lline = shapely.geometry.LineString([[xminAll,yminAll],[xminAll,ymaxAll]])
            geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=WII.crs) #from_epsg(crs_here.split(':')[1]))
            ptsEdgelat =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
            ptsEdgelat = ptsEdgelat[(ptsEdgelat['direction']!='E')&(ptsEdgelat['direction']!='W')]

            ax.yaxis.set_ticks(ptsEdgelat.geometry.centroid.y)
            ax.yaxis.set_ticklabels(ptsEdgelat.display)

            ax.set_title('Ratio WII Area over Industrial Area per Country', pad=20)
            fig.savefig(dirout+'RatioWIIoverIndus.png',dpi=200)
            plt.close(fig)

            #fuel
            mpl.rcdefaults()
            mpl.rcParams['font.size'] = 14
            mpl.rcParams['xtick.labelsize'] = 14
            mpl.rcParams['ytick.labelsize'] = 14
            mpl.rcParams['figure.subplot.left'] = .1
            mpl.rcParams['figure.subplot.right'] = .95
            mpl.rcParams['figure.subplot.top'] = .9
            mpl.rcParams['figure.subplot.bottom'] = .05
            fig = plt.figure(figsize=(10,8))
            ax = plt.subplot(111)
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.1)
            landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
            graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
            #bordersSelection.buffer(-1.e4)[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

            tmp_= np.where(selection['WIIoverFuel'])
            mm = selection.dropna(subset=['WIIoverFuel'])
            mm.plot(ax=ax,cax=cax,column='WIIoverFuel',legend=True,cmap=mpl.colors.LogNorm(vmin=tmp[np.where(tmp_>0)].min(),vmax=np.percentile(tmp_,95)),zorder=2)
            ax.set_xlim(xminAll,xmaxAll)
            ax.set_ylim(yminAll,ymaxAll)
            #set axis
            bbox = shapely.geometry.box(xminAll, yminAll, xmaxAll, ymaxAll)
            geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=WII.crs) #from_epsg(crs_here.split(':')[1]))
            geo['geometry'] = geo.boundary
            ptsEdge =  gpd.overlay(graticule, geo, how = 'intersection', keep_geom_type=False)
            
            lline = shapely.geometry.LineString([[xminAll,ymaxAll],[xmaxAll,ymaxAll]])
            geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=WII.crs) #from_epsg(crs_here.split(':')[1]))
            ptsEdgelon =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
            ptsEdgelon = ptsEdgelon[(ptsEdgelon['direction']!='N')&(ptsEdgelon['direction']!='S')]
            
            ax.xaxis.set_ticks(ptsEdgelon.geometry.centroid.x)
            ax.xaxis.set_ticklabels(ptsEdgelon.display)
            ax.xaxis.tick_top()
            
            lline = shapely.geometry.LineString([[xminAll,yminAll],[xminAll,ymaxAll]])
            geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=WII.crs) #from_epsg(crs_here.split(':')[1]))
            ptsEdgelat =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
            ptsEdgelat = ptsEdgelat[(ptsEdgelat['direction']!='E')&(ptsEdgelat['direction']!='W')]

            ax.yaxis.set_ticks(ptsEdgelat.geometry.centroid.y)
            ax.yaxis.set_ticklabels(ptsEdgelat.display)
            ax.set_title('Ratio WII Area over total Fuel Area per Country', pad=20)
            fig.savefig(dirout+'RatioWIIoverFuel.png',dpi=200)
            plt.close(fig)
            
            #save csv
            #########
            pd.DataFrame(selection.drop(columns='geometry')).to_csv(dirout+'{:s}_info_country.csv'.format(continent))
        '''
        
        #per province
        ############
        print('{:s} per province:'.format(continent))
        selection = bordersSelection[bordersSelection['LEVL_CODE']==0]
        selection = gpd.clip( selection, (xminAll, yminAll, xmaxAll, ymaxAll)).reset_index()
        if continent == 'europe': 
            selection = selection.drop(columns='NAME')
            selection = selection.rename(columns={'NAME_LATN':'NAME'})
        nnC = len(selection)
       
        outgdf = gpd.GeoDataFrame(columns=['id','geometry','WIIoverIndus','WIIoverFuel','IndusAera_ha','WIIAera_ha','ProvinceSize_ha','FuelAera_ha',
                                           'FuelCatAera1_ha','FuelCatAera2_ha','FuelCatAera3_ha','FuelCatAera4_ha','FuelCatAera5_ha',
                                           'nameCountry','nameProvince'], geometry='geometry', crs=WII.crs)
      
        #outgdf['id'] = outgdf['id'].astype(int)
        #for xx in ['WIIoverIndus','WIIoverFuel','IndusAera_ha','WIIAera_ha','ProvinceSize_ha','FuelAera_ha',
        #           'FuelCatAera1_ha','FuelCatAera2_ha','FuelCatAera3_ha','FuelCatAera4_ha','FuelCatAera5_ha',]:
        #    outgdf[xx] = outgdf[xx].astype(float)
        #outgdf['nameCountry'] = outgdf['nameCountry'].astype(int)
        #outgdf['nameProvince'] = outgdf['nameProvince'].astype(int)

        ii = 0
        for ipolyC in range(len(selection)):

            tmp = selection[ipolyC:ipolyC+1]
            tmp['geometry'] = tmp.geometry.buffer(-0.5)

            if continent == 'europe':
                if selection[ipolyC:ipolyC+1]['scalerank'].isnull().values[0]: # NUTS
                    selectionProv = gpd.overlay(tmp, provinces, how = 'intersection', keep_geom_type=False)
                    selectionProv = selectionProv.rename(columns={'NUTS_NAME_2':'name'})
                else: 
                    selectionProv = gpd.overlay(tmp, provincesAll, how = 'intersection', keep_geom_type=False)
                    selectionProv = selectionProv.rename(columns={'NAME_LATN_2':'name'})

            else: 
                selectionProv = gpd.overlay(tmp, provinces, how = 'intersection', keep_geom_type=False)
                selectionProv = selectionProv.rename(columns={'NAME_LATN_2':'name'})

            if selectionProv['name'].isnull().values.any():
                selectionProv.loc[selectionProv['name'].isnull(),'name'] = 'no name'

            selectionProv = selectionProv.reset_index()
            nn = len(selectionProv)
            
            #if selection.loc[ipolyC,'NAME'] != 'Kosovo': continue
            
            for ipoly in range(len(selectionProv)):
                print('{:5.1f}% -- {:5s} | {:05.1f}% -- {:s}                          '.format(100.*ipolyC/nnC, selection.loc[ipolyC,'NAME'], 
                                                                                               100.*ipoly/nn,selectionProv.loc[ipoly,'name']), end='\r')
                sys.stdout.flush()
                sxmin, symin, sxmax, symax = selectionProv[ipoly:ipoly+1].total_bounds
                
                tmp = indus.cx[sxmin:sxmax,symin:symax]
                indus_ =       gpd.overlay(selectionProv[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
            
                tmp = WII.cx[sxmin:sxmax,symin:symax]
                WII_         = gpd.overlay(selectionProv[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
                
                if type(fuelCat_all) is gpd.GeoDataFrame :
                    tmp = fuelCat_all.cx[sxmin:sxmax,symin:symax]
                    fuelCat_all_ = gpd.overlay(selectionProv[ipoly:ipoly+1], tmp, how = 'intersection', keep_geom_type=False)
                    AreaFuelCat = np.zeros([5])
                    for iv in range(1,6): 
                        AreaFuelCat[iv-1] = fuelCat_all_[fuelCat_all_['ICat']==iv].area.sum()*1.e-4

                else:
                    indir = '{:s}/CLC/'.format(dir_data)
                    AreaFuelCat = fuelCatAreaFromraster(indir, selectionProv[ipoly:ipoly+1], selectionProv.loc[ipoly,'name'], xminAll,yminAll, xmaxAll,ymaxAll) 

                totalAreaFuelCat = AreaFuelCat.sum()

                #if totalAreaFuelCat == 0 : 
                #    pdb.set_trace()
                
                #selectionProv.loc[ipoly,'WIIAera_ha'] = WII_.area.sum()*1.e-4
                #selectionProv.loc[ipoly,'IndusAera_ha'] = indus_.area.sum()*1.e-4
                #selectionProv.loc[ipoly,'FuelCatAera_ha'] = totalAreaFuelCat
                #
                #selectionProv.loc[ipoly,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum()
                #selectionProv.loc[ipoly,'WIIoverFuel']  = WII_.area.sum()/(totalAreaFuelCat*1.e4)

                outgdf.loc[ii] = selectionProv.loc[ipoly] # to set the geometry
                
                outgdf.loc[ii,'id'] = ii
                outgdf.loc[ii,'nameCountry'] = selection.loc[ipolyC,'NAME']
                outgdf.loc[ii,'nameProvince'] = selectionProv.loc[ipoly,'name']

                outgdf.loc[ii,'WIIAera_ha'] = WII_.area.sum()*1.e-4
                outgdf.loc[ii,'IndusAera_ha'] = indus_.area.sum()*1.e-4
                outgdf.loc[ii,'FuelAera_ha'] = totalAreaFuelCat
                outgdf.loc[ii,'ProvinceSize_ha'] = selectionProv[ipoly:ipoly+1].area.sum()*1.e-4
                
                outgdf.loc[ii,'WIIoverIndus'] = WII_.area.sum()/indus_.area.sum() if indus_.area.sum() != 0 else np.nan
                outgdf.loc[ii,'WIIoverFuel']  = WII_.area.sum()/(totalAreaFuelCat*1.e4) if totalAreaFuelCat !=0 else np.nan

                outgdf.loc[ii,'FuelCatAera1_ha'] = AreaFuelCat[0]
                outgdf.loc[ii,'FuelCatAera2_ha'] = AreaFuelCat[1]
                outgdf.loc[ii,'FuelCatAera3_ha'] = AreaFuelCat[2]
                outgdf.loc[ii,'FuelCatAera4_ha'] = AreaFuelCat[3]
                outgdf.loc[ii,'FuelCatAera5_ha'] = AreaFuelCat[4]

                if  outgdf.loc[ii,'geometry'] is None: pdb.set_trace()

                #if selection.loc[ipolyC,'NAME'] == 'Kosovo': pdb.set_trace()

                ii+= 1
        
        outgdf['id'] = outgdf['id'].astype(int)
        for xx in ['WIIoverIndus','WIIoverFuel','IndusAera_ha','WIIAera_ha','ProvinceSize_ha','FuelAera_ha',
                   'FuelCatAera1_ha','FuelCatAera2_ha','FuelCatAera3_ha','FuelCatAera4_ha','FuelCatAera5_ha',]:
            outgdf[xx] = outgdf[xx].astype(float)
        outgdf['nameCountry'] = outgdf['nameCountry'].astype(str)
        outgdf['nameProvince'] = outgdf['nameProvince'].astype(str)
        outgdf = outgdf.set_crs(crs_here)
        print('                                                 ', end='\r')



    #plot
    #####
    mpl.rcdefaults()
    mpl.rcParams['font.size'] = 14
    mpl.rcParams['xtick.labelsize'] = 14
    mpl.rcParams['ytick.labelsize'] = 14
    mpl.rcParams['figure.subplot.left'] = .1
    mpl.rcParams['figure.subplot.right'] = .93
    mpl.rcParams['figure.subplot.top'] = .9
    mpl.rcParams['figure.subplot.bottom'] = .05
    #indus
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.1)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)

    tmp_ = np.array(outgdf[~outgdf['WIIoverIndus'].isnull()]['WIIoverIndus'])
    outgdf[~outgdf['WIIoverIndus'].isnull()].plot(ax=ax,cax=cax,column='WIIoverIndus',legend=True, norm=mpl.colors.LogNorm(vmin=tmp_[np.where(tmp_>0)].min(),vmax=np.percentile(tmp_,95)), cmap=mpl.cm.Reds ,zorder=2)
    ax.set_xlim(xminAll,xmaxAll)
    ax.set_ylim(yminAll,ymaxAll)
    #set axis
    bbox = shapely.geometry.box(xminAll, yminAll, xmaxAll, ymaxAll)
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=landNE.crs) #from_epsg(crs_here.split(':')[1]))
    geo['geometry'] = geo.boundary
    ptsEdge =  gpd.overlay(graticule, geo, how = 'intersection', keep_geom_type=False)

    lline = shapely.geometry.LineString([[xminAll,ymaxAll],[xmaxAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=landNE.crs) #from_epsg(crs_here.split(':')[1]))
    ptsEdgelon =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
    ptsEdgelon = ptsEdgelon[(ptsEdgelon['direction']!='N')&(ptsEdgelon['direction']!='S')]

    ax.xaxis.set_ticks(ptsEdgelon.geometry.centroid.x)
    ax.xaxis.set_ticklabels(ptsEdgelon.display)
    ax.xaxis.tick_top()

    lline = shapely.geometry.LineString([[xminAll,yminAll],[xminAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=landNE.crs) #from_epsg(crs_here.split(':')[1]))
    ptsEdgelat =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
    ptsEdgelat = ptsEdgelat[(ptsEdgelat['direction']!='E')&(ptsEdgelat['direction']!='W')]

    ax.yaxis.set_ticks(ptsEdgelat.geometry.centroid.y)
    ax.yaxis.set_ticklabels(ptsEdgelat.display)

    ax.set_title('Ratio WII Area over Industrial Area per Province/State', pad=20)
    fig.savefig(dirout+'RatioWIIoverIndus_province.png',dpi=400)
    plt.close(fig)


    #fuel
    mpl.rcdefaults()
    mpl.rcParams['font.size'] = 14
    mpl.rcParams['xtick.labelsize'] = 14
    mpl.rcParams['ytick.labelsize'] = 14
    mpl.rcParams['figure.subplot.left'] = .1
    mpl.rcParams['figure.subplot.right'] = .93
    mpl.rcParams['figure.subplot.top'] = .9
    mpl.rcParams['figure.subplot.bottom'] = .05
    fig = plt.figure(figsize=(10,8))
    ax = plt.subplot(111)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.1)
    landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
    graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)

    tmp_ = np.array(outgdf[~outgdf['WIIoverFuel'].isnull()]['WIIoverFuel'])
    outgdf[~outgdf['WIIoverFuel'].isnull()].plot(ax=ax,cax=cax,column='WIIoverFuel',legend=True, norm=mpl.colors.LogNorm(vmin=tmp_[np.where(tmp_>0)].min(),vmax=np.percentile(tmp_,95)), cmap=mpl.cm.Reds,zorder=2)
    ax.set_xlim(xminAll,xmaxAll)
    ax.set_ylim(yminAll,ymaxAll)
    #set axis
    bbox = shapely.geometry.box(xminAll, yminAll, xmaxAll, ymaxAll)
    geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=landNE.crs) #from_epsg(crs_here.split(':')[1]))
    geo['geometry'] = geo.boundary
    ptsEdge =  gpd.overlay(graticule, geo, how = 'intersection', keep_geom_type=False)

    lline = shapely.geometry.LineString([[xminAll,ymaxAll],[xmaxAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=landNE.crs) #from_epsg(crs_here.split(':')[1]))
    ptsEdgelon =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
    ptsEdgelon = ptsEdgelon[(ptsEdgelon['direction']!='N')&(ptsEdgelon['direction']!='S')]

    ax.xaxis.set_ticks(ptsEdgelon.geometry.centroid.x)
    ax.xaxis.set_ticklabels(ptsEdgelon.display)
    ax.xaxis.tick_top()

    lline = shapely.geometry.LineString([[xminAll,yminAll],[xminAll,ymaxAll]])
    geo = gpd.GeoDataFrame({'geometry': lline}, index=[0], crs=landNE.crs) #from_epsg(crs_here.split(':')[1]))
    ptsEdgelat =  gpd.overlay(ptsEdge, geo, how = 'intersection', keep_geom_type=False)
    ptsEdgelat = ptsEdgelat[(ptsEdgelat['direction']!='E')&(ptsEdgelat['direction']!='W')]

    ax.yaxis.set_ticks(ptsEdgelat.geometry.centroid.y)
    ax.yaxis.set_ticklabels(ptsEdgelat.display)

    ax.set_title('Ratio WII Area over total Fuel Area per Province/State', pad=20)
    fig.savefig(dirout+'RatioWIIoverFuel_province.png',dpi=400)
    plt.close(fig)

    #save geojson
    #######
    outgdf.to_crs('epsg:4326').to_file(dirout+'{:s}_info_province.geojson'.format(continent), driver='GeoJSON')

    #save csv
    #########
    pd.DataFrame(outgdf.drop(columns='geometry')).to_csv(dirout+'{:s}_info_province.csv'.format(continent))

