import geopandas as gpd
import numpy as np
import sys
import importlib
import pandas as pd 
import pygeos as pg
import os 
import shutil 

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

    continents = ['africa', 'namerica', 'camerica', 'samerica', 'russia', 'oceania', 'europe', 'asia']
    outdir = '{:s}/Maps-Product/World-Final/'.format(dir_data)
    tools.ensure_dir(outdir)


    for ic, continent in enumerate(continents):
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

        gdf = gpd.read_file(indir+'{:s}_info_province.geojson'.format(continent))
    
        if ic == 0: 
            mapProv = gdf.copy()
        else:
            mapProv = pd.concat([mapProv,gdf],ignore_index=True)

        print('')


    mapProv.to_file(outdir+'info_province-world.geojson',driver='GeoJSON')



