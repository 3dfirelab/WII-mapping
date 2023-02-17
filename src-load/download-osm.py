import os 
import wget 
import sys
import sys
import os 
import glob
import shutil
import numpy as np 
import subprocess
import geopandas as gpd
import importlib
import countries as contries_mod
if __name__ == '__main__':

    importlib.reload(contries_mod)
    from countries import countries

    template_url = 'https://download.geofabrik.de/europe/{:s}-latest.osm.pbf'
    dirout = '/mnt/dataEstrella/WII/OSM/PerCountry/'

    #download file
    for country_info in countries: 
        country = country_info[0]
        url = template_url.format('-'.join(country.lower().split(' ')))
        if country == 'Russia': url = url.replace('europe/','')
        if os.path.isfile(dirout+url.split('/')[-1]): continue
        if len( glob.glob( dirout+url.split('/')[-1].split('.osm')[0]+'*.osm.pbf') ) > 0: continue 
        print(url)
        wget.download(url, dirout )
        print('')

    #split file in tiles
    indir = '/mnt/dataEstrella/WII/Boundaries/NUTS/'
    borders = gpd.read_file(indir+'NUTS_RG_01M_2021_4326.geojson')
    xminEU,yminEU, xmaxEU,ymaxEU = [-31., 24.505457173625324, 99.52727619009086, 80.51193780175987]
    
    countries = np.array(countries)
    for ic in range(countries.shape[0]):
        countries[ic,0]= '-'.join(countries[ic,0].lower().split(' '))

    indir = '/mnt/dataEstrella/WII/OSM/PerCountry/'
    outdir = '/mnt/dataEstrella/WII/OSM/PerCountry/'
    osmfiles = sorted(glob.glob(indir+'*latest.osm.pbf'))

    template_osmosis_main = 'osmosis --read-pbf {:s} --tee {:d} '
    template_osmosis_bb   = '--bounding-box left={:.4f} right={:.4f} bottom={:.4f} top={:.4f} --write-pbf {:s} ' 

    for osmfile in osmfiles: 
        country =os.path.basename(osmfile).split('-latest')[0]
        
        #load borders
        idx_ = np.where(countries[:,0] == country)
        country_code = countries[idx_[0][0],1]
        country_code2 = countries[idx_[0][0],2]

        if country_code != None:
            if country_code2 == None:
                borders_ = borders[(borders['LEVL_CODE']==1)&(borders['CNTR_CODE']==country_code)]
            elif country_code2[:2] == '!=':
                borders_ = borders[(borders['LEVL_CODE']==1)&(borders['CNTR_CODE']==country_code)&(borders['NUTS_ID']!=country_code2[2:])]
            else: 
                borders_ = borders[(borders['LEVL_CODE']==1)&(borders['CNTR_CODE']==country_code)&(borders['NUTS_ID']==country_code2)]
            borders_ = borders_.cx[xminEU:xmaxEU, yminEU:ymaxEU]
        else: 
            borders_ = None

        
        if borders_ is None : 
            extent_ll=[[xminEU,xmaxEU,yminEU,ymaxEU]]
        else: 
            xmin_, ymin_, xmax_, ymax_ = borders_.total_bounds
          
            xmin_ = max([xmin_,xminEU])
            xmax_ = min([xmax_,xmaxEU])
            ymin_ = max([ymin_,yminEU])
            ymax_ = min([ymax_,ymaxEU])

            dd = 3
            xx = np.arange(xmin_,xmax_+dd,dd)
            yy = np.arange(ymin_,ymax_+dd,dd)
            
            extent_ll = []
            for x1, x2 in zip(xx[:-1],xx[1:]):
                for y1, y2 in zip(yy[:-1],yy[1:]):
                    extent_ll.append( [x1,x2,y1,y2] ) 

        nbreTile = len(extent_ll)
        if nbreTile> 1:
            
            #filesthere = glob.glob(osmfile.split('.os')[0]+'_*.osm.pbf')
            #sys.exit()
            #if len(filesthere) == nbreTile: continue

            osmosis_bb = ''
            for it, extent_ll_ in enumerate(extent_ll):

                x1,x2,y1,y2 = extent_ll_
                osmosis_bb += template_osmosis_bb.format(x1,x2,y1,y2,'_{:d}.o'.format(it).join(osmfile.split('.o')))

            cmd = template_osmosis_main.format(osmfile,nbreTile) + osmosis_bb
            print('  {:s} split in {:d} ...'.format(country,nbreTile), end='\r')
            process = subprocess.Popen(cmd.strip().split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()

            os.remove(osmfile)
            print('  {:s} split in {:d}    '.format(country,nbreTile))


        else: 
            print('  {:s} not split'.format(country))


