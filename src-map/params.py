

def load_param(continent):

    if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
        bufferBorder = -1800
        distgroup = 5.e3

    elif continent == 'asia':
        xminAll,xmaxAll = -1.057e7, -2.5e5
        yminAll,ymaxAll = -1.74e6, 6.66e6
        crs_here = 'epsg:8859'
        bufferBorder = -10000
        distgroup = 1.e3
    
    elif continent == 'namerica':
        xminAll,xmaxAll = 1.95e6,  9.06e6
        yminAll,ymaxAll = -2.98e6,  5.90e6
        crs_here = 'epsg:3347'
        #xminAll,xmaxAll = -4.61e6,  2.62e6
        #yminAll,ymaxAll = -4.19e6,  4.18e6
        #crs_here = '+proj=laea +lon_0=-447.19 +lat_0=49.57 +datum=WGS84 +units=m +no_defs'
        #from https://projectionwizard.org/#

        bufferBorder = -10000
        distgroup = 1.e3

    params = {'xminAll': xminAll,
              'xmaxAll': xmaxAll, 
              'yminAll': yminAll,
              'ymaxAll': ymaxAll, 
              'crs_here': crs_here, 
              'bufferBorder': bufferBorder, 
              'distgroup': distgroup, 
              }

    return params
