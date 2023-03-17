import rasterio
import geopyspark as gps
import numpy as np
import glob 
from pyspark import SparkContext
import sys

conf = gps.geopyspark_conf(master="local[*]", appName="sentinel-ingest-example")
pysc = SparkContext(conf=conf)

indir = '/home/paugam/Downloads/S2A_MSIL2A_20230303T103931_N0509_R008_T31TDG_20230303T182400.SAFE/GRANULE/L2A_T31TDG_A040188_20230303T104759/IMG_DATA/R10m/'

jp2s = glob.glob(indir+'*.jp2') 
arrs = []

for jp2 in jp2s:
    with rasterio.open(jp2) as f:
        arrs.append(f.read(1))

data = np.array(arrs, dtype=arrs[0].dtype)

# Create an Extent instance from rasterio's bounds
extent = gps.Extent(*f.bounds)

# The EPSG code can also be obtained from the information read in via rasterio
projected_extent = gps.ProjectedExtent(extent=extent, epsg=int(f.crs.to_dict()['init'][5:]))

# Projection information from the rasterio file
f.crs.to_dict()

# The projection information formatted to work with GeoPySpark
int(f.crs.to_dict()['init'][5:])

# We can create a Tile instance from our multiband, raster array and the nodata value from rasterio
tile = gps.Tile.from_numpy_array(numpy_array=data, no_data_value=f.nodata)

# Now that we have our ProjectedExtent and Tile, we can create our RDD from them
rdd = pysc.parallelize([(projected_extent, tile)])

# While there is a time component to the data, this was ignored for this tutorial and instead the focus is just
# on the spatial information. Thus, we have a LayerType of SPATIAL.
raster_layer = gps.RasterLayer.from_numpy_rdd(layer_type=gps.LayerType.SPATIAL, numpy_rdd=rdd)


