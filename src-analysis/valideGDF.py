import geopandas as gpd 
import numpy as np 
import matplotlib.pyplot as plt
from shapely.validation import make_valid, explain_validity
import sys 
import importlib
import warnings

#homebrewed
sys.path.append('../src-map/')
import tools
import params

if __name__ == '__main__':


    dir_data = tools.get_dirData()

    importlib.reload(tools)
    importlib.reload(params)

    #continents = ['africa', 'namerica', 'samerica', 'russia', 'asia']
    continents = ['asia']
    
    indir = '{:s}/Maps-Product/World-Final/'.format(dir_data)

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
            
        indir = '{:s}/Maps-Product/World-Final/'.format(dir_data,)
        

        gdf = gpd.read_file(indir+'./WII-{:s}.geojson'.format(continent))

        gdf.geometry = gdf.apply(lambda row: make_valid(row.geometry) if not row.geometry.is_valid else row.geometry, axis=1)
        
        for index, row in gdf[(gdf.geom_type != 'Polygon') & (gdf.geom_type!='MultiPolygon')].iterrows():
            with warnings.catch_warnings(record=True) as w:
                gdf.at[index,'geometry'] =  gdf[index:index+1].geometry.buffer(1.e-10).unary_union 

        gdf.to_file( indir+'./WII-{:s}-valide.geojson'.format(continent) )
        print('')
