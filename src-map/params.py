

def load_param(continent):

    if continent == 'europe':
        xminAll,xmaxAll = 2500000., 7400000.
        yminAll,ymaxAll = 1400000., 5440568.
        crs_here = 'epsg:3035'
        bufferBorder = -1800
        distgroup = 5.e3

    elif continent == 'asia':
        xminAll,xmaxAll = -1.315e7, -6.e4
        yminAll,ymaxAll = -1.79e6, 7.93e6
        crs_here = 'epsg:8859'
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
