

import sys
import os 
#os.environ['USE_PYGEOS'] = '0'
import pandas as pd 
import geopandas as gpd
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
import glob
import shutil
import warnings
import importlib 

#homebrwed
import countries as contries_mod
sys.path.append('../src-map/')
import params
import tools

if __name__ == '__main__':
   
    importlib.reload(params)
    continent = 'namerica'
    dir_data = tools.get_dirData()
    
    print('continent = ', continent)

    importlib.reload(contries_mod)
    from countries import europe, asia, namerica
    if continent == 'europe': 
        countries_selection = np.array(europe)

    elif continent == 'asia': 
        countries_selection = np.array(asia)
    
    elif continent == 'namerica': 
        countries_selection = namerica
    countries_selection = np.array(countries_selection)

    params = params.load_param(continent)
    xminAll,xmaxAll = params['xminAll'], params['xmaxAll']
    yminAll,ymaxAll = params['yminAll'], params['ymaxAll']
    crs_here        = params['crs_here']
    bufferBorder    = params['bufferBorder']

    indir = '{:s}Boundaries/'.format(dir_data)
    bordersNE = gpd.read_file(indir+'NaturalEarth_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
    
    continentMask = None
    for country_code in countries_selection[:,1]: 
        
        if len(country_code.split(','))>1:
            country_code_ = country_code.split(',')
            condition = (bordersNE['SOV_A3']==country_code_[0])
            for country_code__ in country_code_[1:]:
                condition |= (bordersNE['SOV_A3']==country_code__)
            borders_ = bordersNE[condition]
        else:
            borders_ = bordersNE[bordersNE['SOV_A3']==country_code]

        if continentMask is None:
            continentMask=borders_
        else:
            continentMask = pd.concat([continentMask,borders_])
            
    continentMask = continentMask.to_crs(crs_here)
    continentMask['LEVL_CODE'] = 0
    continentMask.to_file(indir+'mask_{:s}.geojson'.format(continent),driver='GeoJSON')
    
    if continentMask.crs.to_epsg() is None: 
        with open(indir+'mask_{:s}.prj'.format(continent),'w') as f:
            f.write(continentMask.crs.to_wkt())
