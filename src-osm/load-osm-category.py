import sys
import os 
#os.environ['USE_PYGEOS'] = '0'
import pandas 
import geopandas
import numpy as np 
import matplotlib as mpl
import matplotlib.pyplot as plt
import pyrosm


if __name__ == '__main__':

    indir = '/mnt/dataEstrella/OSM/'
    extent_ll = [3.75, 43.4, 4.17, 43.7]
    osm = pyrosm.OSM(filepath=indir+'./cataluna-latest.osm.pbf')

    #custom_filter={'building': ['industrial']}
    #buildings = osm.get_buildings(custom_filter=custom_filter)

    custom_filter={'natural': ['wood']}
    wood = osm.get_natural(custom_filter=custom_filter)
    wood = wood[wood.geom_type!='Point'] 

    wood.to_file(indir+'wood.shp')



