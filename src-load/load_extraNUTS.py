

import sys
import os 
#os.environ['USE_PYGEOS'] = '0'
import pandas as pd 
import geopandas as gpd
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
import pyrosm
import glob
import shutil
import warnings



if __name__ == '__main__':
    
    extraCountries = ['Andorra', 'Monaco', 'Bosnia and Herzegovina', 'Kosovo' ]

    indir = '/mnt/dataEstrella/WII/Boundaries/'
    bordersNE = gpd.read_file(indir+'NaturalEarth_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
    
    extra = None
    for country in extraCountries: 
        
        borders_ = bordersNE[bordersNE['SOVEREIGNT']==country]
        if extra is None:
            extra=borders_
        else:
            extra = pd.concat([extra,borders_])
            
   
    extra['LEVL_CODE'] = 0
    extra.to_file(indir+'noNUTS.geojson',driver='GeoJSON')
