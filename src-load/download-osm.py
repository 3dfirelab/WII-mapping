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

#homebrwed
sys.path.append('../src-map/')
import tools

if __name__ == '__main__':

    continent = 'africa'
    dir_data = tools.get_dirData()

    print('continent = ', continent)

    importlib.reload(contries_mod)
    from countries import europe, asia, namerica, samerica, camerica, africa
    
    if continent == 'europe': 
        countries_selection = europe
        continent_url = countries_selection
    elif continent == 'asia': 
        countries_selection = asia
        continent_url = countries_selection
    elif continent == 'namerica': 
        countries_selection = namerica
        continent_url = 'north-america'
    elif continent == 'samerica': 
        countries_selection = samerica
        continent_url = 'south-america'
    elif continent == 'camerica': 
        countries_selection = camerica
        continent_url = 'central-america'
    elif continent == 'africa': 
        countries_selection = africa
        continent_url = 'africa'

    template_url = 'https://download.geofabrik.de/{:s}'.format(continent_url)+'/{:s}-latest.osm.pbf'
    template_url2 = 'https://download.openstreetmap.fr/extracts/{:s}'.format(continent_url)+'/{:s}-latest.osm.pbf'
    dirout = '{:s}OSM/PerCountry-{:s}/'.format(dir_data,continent)
    tools.ensure_dir(dirout)

    def getomspbf(template_url,dirout,spaceCharacter='-'):
        url = template_url.format(spaceCharacter.join(country.lower().split(' ')))
        if country == 'Russia': url = url.replace('europe/','')
        if 'Malaysia' in country: url = url.replace(',','').replace('and-','')
        if 'Haiti' in country_info[0]: url = url.replace('haiti-and-dominican-republic','haiti-and-domrep')
        if 'congo-(republic/brazzaville)' in url: url = url.replace('congo-(republic/brazzaville)', 'congo-brazzaville')
        if 'congo-(democratic-republic/kinshasa)' in url: url = url.replace('congo-(democratic-republic/kinshasa)', 'congo-democratic-republic')
        if 'saint-helena' in url: url = url.replace(',','')

        if os.path.isfile(dirout+url.split('/')[-1]): 
            return url.split('/')[-1].split('-latest.')[0]
        if len( glob.glob( dirout+url.split('/')[-1].split('.osm')[0]+'*.osm.pbf') ) > 0:
            return url.split('/')[-1].split('-latest.')[0]
        if country_info[0] == 'France':  url = url.replace('south-america','europe')
        if country_info[0] == 'France':  url = url.replace('central-america','europe')
        print(url)
        wget.download(url, dirout )
        print('')

        return url.split('/')[-1].split('-latest.')[0]


    #download file
    countries_here = np.array(countries_selection)
    for ic, country_info in enumerate(countries_selection): 
        country = country_info[0]
        try: 
           countries_here_ = getomspbf(template_url,dirout)
        except: 
           countries_here_ = getomspbf(template_url2,dirout,spaceCharacter='_')

        countries_here[ic,0] =  countries_here_

    #split file in tiles
    if continent == 'europe':
        indir = '{:s}Boundaries/NUTS/'.format(dir_data)
        borders = gpd.read_file(indir+'NUTS_RG_01M_2021_4326.geojson')
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [-31., 24.505457173625324, 99.52727619009086, 80.51193780175987]
    elif continent == 'asia':
        indir = '{:s}Boundaries//'.format(dir_data)
        borders = gpd.read_file(indir+'NaturalEarth_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [28.7, -14.9, 188, 87.]
    elif continent == 'namerica':
        indir = '{:s}Boundaries//'.format(dir_data)
        borders = gpd.read_file(indir+'NaturalEarth_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [-180, -13.0, -21, 90.]
    elif continent == 'samerica':
        indir = '{:s}Boundaries//'.format(dir_data)
        borders = gpd.read_file(indir+'NaturalEarth_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [-95, -65.0, -30, 14.]
    elif continent == 'camerica':
        indir = '{:s}Boundaries//'.format(dir_data)
        borders = gpd.read_file(indir+'NaturalEarth_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [-95, 5.0, -50, 30.]
    elif continent == 'africa':
        indir = '{:s}Boundaries//'.format(dir_data)
        borders = gpd.read_file(indir+'NaturalEarth_10m_admin_0_countries/ne_10m_admin_0_countries.shp')
        xminContinent,yminContinent, xmaxContinent,ymaxContinent = [-25, -40.0, 55, 38.]
    
    '''
    countries_here = np.array(countries_selection)
    for ic in range(countries_here.shape[0]):
        countries_here[ic,0]= '-'.join(countries_here[ic,0].lower().split(' '))

        if 'malaysia' in countries_here[ic,0]: countries_here[ic,0] = countries_here[ic,0].replace(',','').replace('and-','')
    '''

    indir = '{:s}OSM/PerCountry-{:s}/'.format(dir_data, continent)
    outdir = '{:s}OSM/PerCountry-{:s}/'.format(dir_data, continent)
    osmfiles = sorted(glob.glob(indir+'*latest.osm.pbf'))

    template_osmosis_main = 'osmosis --read-pbf {:s} --tee {:d} '
    template_osmosis_bb   = '--bounding-box left={:.4f} right={:.4f} bottom={:.4f} top={:.4f} --write-pbf {:s} ' 

    for osmfile in osmfiles: 
        country =os.path.basename(osmfile).split('-latest')[0]
        
        #load borders
        idx_ = np.where(countries_here[:,0] == country)
        country_code = countries_here[idx_[0][0],1]
        country_code2 = countries_here[idx_[0][0],2]

        if country_code != None:
            if continent == 'europe':
                if country_code2 == None:
                    borders_ = borders[(borders['LEVL_CODE']==1)&(borders['CNTR_CODE']==country_code)]
                elif country_code2[:2] == '!=':
                    borders_ = borders[(borders['LEVL_CODE']==1)&(borders['CNTR_CODE']==country_code)&(borders['NUTS_ID']!=country_code2[2:])]
                else: 
                    borders_ = borders[(borders['LEVL_CODE']==1)&(borders['CNTR_CODE']==country_code)&(borders['NUTS_ID']==country_code2)]
            
            elif (continent == 'asia') | (continent=='namerica')| (continent=='samerica')| (continent=='camerica')| (continent=='africa'):
                if len(country_code.split(','))>1:
                    country_code_ = country_code.split(',')
                    condition = (borders['SOV_A3']==country_code_[0])
                    for country_code__ in country_code_[1:]:
                        condition |= (borders['SOV_A3']==country_code__)
                    borders_ = borders[condition]
                else:
                    borders_ = borders[borders['SOV_A3']==country_code]
                

            borders_ = borders_.cx[xminContinent:xmaxContinent, yminContinent:ymaxContinent]
        
        else: 
            borders_ = None

        if (borders_ is None)  | (len(borders_)==0): 
            extent_ll=[[xminContinent,xmaxContinent,yminContinent,ymaxContinent]]
        else: 
            xmin_, ymin_, xmax_, ymax_ = borders_.total_bounds
          
            xmin_ = max([xmin_,xminContinent])
            xmax_ = min([xmax_,xmaxContinent])
            ymin_ = max([ymin_,yminContinent])
            ymax_ = min([ymax_,ymaxContinent])

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


