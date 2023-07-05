import geopandas as gpd
import numpy as np
import sys
import importlib
import pandas as pd 
import pygeos as pg
import os 
import shutil 
from shapely.validation import make_valid, explain_validity

#homebrewed
sys.path.append('../src-map/')
import tools
import params

#################
if __name__ == '__main__':
#################

    dir_data = tools.get_dirData()

    importlib.reload(tools)
    importlib.reload(params)

    continents = ['africa', 'namerica', 'camerica', 'samerica', 'europe', 'russia', 'oceania', 'asia', 'easteurope']
    outdir = '{:s}/Maps-Product/World-Final/'.format(dir_data)
    tools.ensure_dir(outdir)

    WII_global = gpd.GeoDataFrame(columns=['area_ha', 'geometry', 'continent'], geometry='geometry', crs='EPSG:4326')

    for continent in continents:
    
        print(continent, end=' ... ')
        sys.stdout.flush()
        params_ = params.load_param(continent)
        xminAll,xmaxAll = params_['xminAll'], params_['xmaxAll']
        yminAll,ymaxAll = params_['yminAll'], params_['ymaxAll']
        crs_here        = params_['crs_here']
        bufferBorder    = params_['bufferBorder']
        distgroup       = params_['distgroup']
        lonlat_bounds = params_['lonlat_bounds']
        gratreso        = params_['gratreso']
            
        indir = '{:s}/Maps-Product/{:s}/'.format(dir_data,continent)
        
        indus = tools.my_read_file(indir+'industrialZone_osmSource.geojson')
        
        if os.path.isfile(indir+'WII-unary_union.geojson'):
            WII_ = tools.my_read_file(indir+'WII-unary_union.geojson')
            print (' loaded')
            sys.stdout.flush()
        else:
            print(' run unary_union ...', end='')
            sys.stdout.flush()
            WII_ = tools.my_read_file(indir+'WII.geojson')

            #keep single overlap
            # define a function that rounds the coordinates of every geometry in the array
            round = np.vectorize(lambda geom: pg.apply(geom, lambda g: g.round(3)))
            WII_.geometry = round(WII_.geometry.values.data)
            tmp_ = WII_.buffer(0.0)
            WII_ = gpd.GeoDataFrame(geometry=[tmp_.unary_union], crs=WII_.crs).explode( index_parts=False ).reset_index( drop=True )
            #WII_.geometry = WII_.buffer(-0.01)
       
            #to force remove indus from WII
            WII_ = WII_.overlay(indus, how = 'difference', keep_geom_type=False)

            WII_['area_ha'] = WII_.area * 1.e-4
            WII_['continent'] = continent

            WII_.geometry = WII_.apply(lambda row: make_valid(row.geometry) if not row.geometry.is_valid else row.geometry, axis=1)
        
            for index, row in WII_[(WII_.geom_type != 'Polygon') & (WII_.geom_type!='MultiPolygon')].iterrows():
                with warnings.catch_warnings(record=True) as w:
                    WII_.at[index,'geometry'] =  WII_[index:index+1].geometry.buffer(1.e-10).unary_union 



            WII_.to_file(indir+'WII-unary_union.geojson', driver='GeoJSON')
            if os.path.isfile(indir+'WII.prj'):
                shutil.copy(indir+'WII.prj', indir+'WII-unary_union.prj')
            print ('done')
            sys.stdout.flush()

        WII_wgs = WII_[['area_ha','geometry']].to_crs('epsg:4326')
        WII_wgs.to_file(outdir+'WII-{:s}.geojson'.format(continent),driver='GeoJSON')
    
        WII_global = pd.concat([WII_global,WII_wgs],ignore_index=True)
        
    print('WII_global number of features x attributes = ',  WII_global.shape)
    WII_global.to_file(outdir+'WII-world.geojson',driver='GeoJSON')
