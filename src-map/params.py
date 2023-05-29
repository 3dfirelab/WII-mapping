import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

def load_param(continent):

    if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
        bufferBorder = -1800
        distgroup = 5.e3
        lonlat_bounds = None # not necessary here, this is to plot land background 

    elif continent == 'asia':
        xminAll,xmaxAll = -1.057e7, -2.5e5
        yminAll,ymaxAll = -1.74e6, 6.66e6
        crs_here = 'epsg:8859'
        bufferBorder = -10000
        distgroup = 1.e3
        lonlat_bounds = None # not necessary here, this is to plot land background 
    
    elif continent == 'namerica':
        lonlat_bounds = [[-180,5,10,90],[150,60,180,90]]
        xminAll,xmaxAll = 1.95e6,  9.06e6
        yminAll,ymaxAll = -2.98e6,  5.90e6
        crs_here = 'epsg:3347'
        #xminAll,xmaxAll = -4.61e6,  2.62e6
        #yminAll,ymaxAll = -4.19e6,  4.18e6
        #crs_here = '+proj=laea +lon_0=-447.19 +lat_0=49.57 +datum=WGS84 +units=m +no_defs'
        #from https://projectionwizard.org/#
        #crs_here='ESRI:102008'
        #crs_here='+proj=aea +lat_0=40 +lon_0=-96 +lat_1=20 +lat_2=60 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs +type=crs'
        #xminAll,xmaxAll = -6859872.43, 4627500.55 
        #yminAll,ymaxAll = -1870790.97, 5421010.03

        bufferBorder = -10000
        distgroup = 1.e3
    
    elif continent == 'samerica':
        #lonlat_bounds = [[-180,5,10,90],],
        xminAll,xmaxAll = -9.8e5,  6.51e6
        yminAll,ymaxAll = -6.55e6,  2.11e6
        crs_here = 'epsg:31971'

        bufferBorder = -5000
        distgroup = 1.e3
        lonlat_bounds = [[-105., -60.0, -20., 20.]] # not necessary here, this is to plot land background 
    
    elif continent == 'camerica':
        #lonlat_bounds = [[-180,5,10,90],],
        xminAll,xmaxAll = -3.e5,  4.004e6
        yminAll,ymaxAll = 5.55e5,  3.15e6
        crs_here = 'epsg:31970'

        bufferBorder = -1000
        distgroup = 1.e3
        lonlat_bounds = [[-95, 5.0, -50, 50.]] # no
    
    elif continent == 'africa':
        #lonlat_bounds = [[-180,5,10,90],],
        xminAll,xmaxAll = -5.15e6,  4.08e6
        yminAll,ymaxAll = -1.66e6,  6.7e6
        crs_here = '+proj=chamb +lat_1=22 +lon_1=0 +lat_2=22 +lon_2=45 +lat_3=-22 +lon_3=22.5 +datum=WGS84 +type=crs'

        bufferBorder = -10000
        distgroup = 1.e3
        lonlat_bounds = [[-25, -40.0, 55, 38.]] # no


    params = {'xminAll': xminAll,
              'xmaxAll': xmaxAll, 
              'yminAll': yminAll,
              'ymaxAll': ymaxAll, 
              'crs_here': crs_here, 
              'bufferBorder': bufferBorder, 
              'distgroup': distgroup, 
              'lonlat_bounds':lonlat_bounds,
              }

    return params
