import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import numpy as np 
import sys
from rasterio.mask import mask
import geopandas as gpd 
import importlib
import shapely
import pdb 
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm

sys.path.append('../src-load/')
sys.path.append('../src-map/')
import tools 
glc = importlib.import_module("load-glc-category")

if __name__ == '__main__':
    
    continent = 'europe'
    filein = '/mnt/data/WII/TrueColor/2023-03-03-00 00_2023-03-03-23 59_Sentinel-2_L2A_True_color.tiff'
    xminAll,xmaxAll = 2500000., 7400000.
    yminAll,ymaxAll = 1400000., 5440568.
    crs_here = 'epsg:3035'
    distgroup = 5.e3
    xminHere,xmaxHere = 3.6370e6, 3.6760e6 
    yminHere,ymaxHere = 2.0805e6, 2.1159e6 
    
    #industrial zone
    indir = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)
    indusAll = gpd.read_file(indir+'industrialZone_osmSource.geojon')
    

    dirout = '/mnt/dataEstrella/WII/Maps-Product/{:s}/'.format(continent)

    with rasterio.open(filein) as src:
        
        #clip
        bb = 2000
        bbox = shapely.geometry.box(xminHere-bb, yminHere-bb, xmaxHere+bb, ymaxHere+bb)
        geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=crs_here)
        geo = geo.to_crs(crs='epsg:4326')
        coords = glc.getFeatures(geo)
        data_, src_transform = mask(src, shapes=coords, crop=True)
       
        data_out = []
        for xx in range(3):
            band_, transform_dst = tools.reproject_raster(data_[xx], geo.total_bounds , src_transform, geo.crs, crs_here, resolution=60)
            
            if xx == 0: 
                transformer = rasterio.transform.AffineTransformer(transform_dst)
                nx,ny = band_.shape
                dst_bounds = (*transformer.xy(0, 0), *transformer.xy(nx, ny))

            data_out.append(band_)

    data_out = np.array(data_out, dtype=np.uint8)


    #data_out = np.transpose(src.read([1,2,3]),[1,2,0])
    data_out = np.transpose(data_out,[1,2,0])
    norm = (data_out * (255 / np.max(data_out))).astype(np.uint8)
    
    fig = plt.figure(figsize=(9,9))
    ax = plt.subplot(111)
    #ax.imshow(norm,extent=(xminHere,xmaxHere,yminHere,ymaxHere))
    ax.imshow(data_out, extent=(dst_bounds[0],dst_bounds[2],dst_bounds[3],dst_bounds[1]), alpha=0.85)
    indusAll.cx[xminHere:xmaxHere, yminHere:ymaxHere].plot(ax=ax, facecolor='k', edgecolor='k', linewidth=.2,zorder=2,)

    ax.set_xlim(xminHere,xmaxHere)
    ax.set_ylim(yminHere,ymaxHere)
    ax.set_axis_off()
    
    fontprops = fm.FontProperties(size=10)
    scalebar = AnchoredSizeBar(ax.transData,
                               3000, '3 km', 'upper right', 
                               pad=.3,
                               color='k',
                               frameon=True,
                               size_vertical=10,
                               fontproperties=fontprops)

    ax.add_artist(scalebar)

    fig.savefig(dirout+'ZoomIndusSentinel.png',dpi=200)
    plt.close(fig)

