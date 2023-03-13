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
import pdb 
import pyproj
from fiona.crs import from_epsg
import socket 
import numpy as np 

#homebrewed
import tools

warnings.filterwarnings("ignore")

if __name__ == '__main__':

    continent = 'europe'
    flag_onlyplot = False
    flag_loopIndus = ''
    if socket.gethostname() == 'pc70682': flag_loopIndus = 'inverse'
    if socket.gethostname() == 'ubu':     flag_loopIndus = 'center'

    importlib.reload(tools)
    
    if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
        distgroup = 5.e3
    elif continent == 'asia':
        xminAll,xmaxAll = -1.315e7, -6.e4
        yminAll,ymaxAll = -1.79e6, 7.93e6
        crs_here = 'epsg:3832'
        distgroup = 1.e3
 
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

    #load graticule
    gratreso = 15
    graticule = gpd.read_file(indir+'NaturalEarth_graticules/ne_110m_graticules_{:d}.shp'.format(gratreso))
    graticule = graticule.to_crs(crs_here)

    #industrial zone
    indir = '/mnt/dataEstrella/WII/IndustrialZone/{:s}/'.format(continent)
    indusFiles = sorted(glob.glob(indir+'*.geojson'))
    if flag_loopIndus == 'reverse': indusFiles = indusFiles[::-1]
    if flag_loopIndus == 'center' : indusFiles = list( np.roll( np.array(indusFiles), len(indusFiles)//2) )

    dirout = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
   
    if os.path.isfile(dirout+'WII.geojon'):
        print ('load WII ...')
        WII = gpd.read_file(dirout+'WII.geojon')


    else:
        if continent == 'europe':
            #CLC cat for europe
            print('load clc ...', end='')
            sys.stdout.flush()
            indir = '/mnt/dataEstrella/WII/FuelCategories-CLC/{:s}/'.format(continent)
            #idxclc = [1]
            #print('  *** warning: only load cat 1 ***' )
            idxclc = range(1,6)
            fuelCat_all = []
            for iv in idxclc:
                fuelCat_ = gpd.read_file(indir+'fuelCategory{:d}.geojson'.format(iv))
                fuelCat_ = fuelCat_.to_crs(crs_here)
                fuelCat_all.append(fuelCat_)
            print(' done')
   
        elif continent == 'asia':
            idxclc = range(1,6)
            fuelCat_all = [None]*len(idxclc)

        WII_tot = None

        for indusFile in indusFiles:
            
            WIIFile = dirout+'WII-perTyle/WII{:s}.geojon'.format(
                         os.path.basename(indusFile).split('trial-')[1].split('.geo')[0])
            if os.path.isfile(WIIFile):
                print('{:s} '.format(os.path.basename(indusFile)), end='')
                WII = gpd.read_file(WIIFile)
                print ('... loaded', end='')
            else:
                if flag_onlyplot: continue
                print('{:s} shape'.format(os.path.basename(indusFile)), end='')

                WII = None
                indus = gpd.read_file(indusFile)
                indus = indus.to_crs(crs_here)

                indus['area_ha'] = indus['geometry'].area/ 10**4
                indus = indus[indus['area_ha']>1]
                print(' ', indus.shape)
                
                if indus.shape[0] == 0:
                    continue

                elif indus.shape[0]>1:
                    indus['group'] = tools.cluster_shapes_by_distance(indus, distgroup)
                
                else: 
                    indus['group'] = 0 

                #print('nbre group :',indus['group'].max()+1)
                #indus['group'] = indus.group.astype(str)
                #indus.plot(column='group', legend=True)
                #plt.show()
                #sys.exit()

                indir = '/mnt/dataEstrella/WII/FuelCategories-CLC/'

                for iv in idxclc:
                    WII = tools.buildWII(WII, iv, fuelCat_all[iv-1], indus, continent)

                WII.to_file(WIIFile, driver='GeoJSON')
            
            print ('WII area_ha = ', WII.area.sum()*1.e-4 )
            
            if WII_tot is None: 
                WII_tot = WII
            else:
                WII_tot = pd.concat([WII_tot, WII])

        if socket.gethostname() == 'moritz':
            WII_tot.to_file(dirout+'WII.geojon',driver='GeoJSON')
   
    if socket.gethostname() == 'moritz':
    
        #plot
        fig = plt.figure(figsize=(10,8))
        ax = plt.subplot(111)
        landNE.plot(ax=ax,facecolor='0.9',edgecolor='None',zorder=1)
        graticule.plot(ax=ax, color='lightgrey',linestyle=':',alpha=0.95,zorder=3)
        bordersSelection[bordersSelection['LEVL_CODE']==0].plot(ax=ax,facecolor='0.75',edgecolor='None',zorder=2)

        WII_tot.plot(ax=ax, facecolor='hotpink', edgecolor='hotpink', linewidth=.2,zorder=4)
        
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
        
        ax.set_title('Wildand Industrial Interface', pad=30)
        fig.savefig(dirout+'WII.png',dpi=200)
        plt.close(fig)


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
