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

#homebrewed
import tools

warnings.filterwarnings("ignore")

if __name__ == '__main__':

    importlib.reload(tools)
    
    xminEU,yminEU, xmaxEU,ymaxEU = [-31., 24.505457173625324, 99.52727619009086, 80.51193780175987]
    
    #borders
    indir = '/mnt/dataEstrella/WII/Boundaries/NUTS/'
    borders = gpd.read_file(indir+'NUTS_RG_01M_2021_4326.geojson')
    borders = borders.to_crs('epsg:3035')


    #industrial zone
    indir = '/mnt/dataEstrella/WII/IndustrialZone/'
    indusFiles = sorted(glob.glob(indir+'*.geojson'))
   

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
        fuelCat_all.append(fuelCat_)
    print(' done')

    WII = None

    dirout = '/mnt/dataEstrella/WII/IndustrialZone_level2/'
    for indusFile in indusFiles:
        indus = gpd.read_file(indusFile)
        indus = indus.to_crs('epsg:3035')

        indus['area_ha'] = indus['geometry'].area/ 10**4
        indus = indus[indus['area_ha']>1]
        print('{:s} shape'.format(os.path.basename(indusFile)), indus.shape)

        if indus.shape[0]>10:
            indus['group'] = tools.cluster_shapes_by_distance(indus, 5.e3,)
        else: 
            indus['group'] = 0 

        #print('nbre group :',indus['group'].max()+1)
        #indus['group'] = indus.group.astype(str)
        #indus.plot(column='group', legend=True)
        #plt.show()
        #sys.exit()

        indir = '/mnt/dataEstrella/WII/FuelCategories-CLC/'

        for iv in idxclc:
            WII = tools.buildWII(WII, iv, fuelCat_all[iv-1], indus)


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
