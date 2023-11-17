import json 
import sys
import importlib 

#homebrewed
sys.path.append('../src-map/')
import tools
import params


if __name__ == '__main__':

    lines = []
    lines.append('#!/bin/bash\n')
    lines.append('export MAPBOX_ACCESS_TOKEN=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg\n')
    lines.append('source ~/anaconda3/bin/activate mapbox')
    lines.append('\n')


    dir_data = tools.get_dirData()

    importlib.reload(tools)
    importlib.reload(params)
    #continents = ['africa']
    #continents = ['africa', 'namerica', 'camerica', 'samerica', 'russia', 'asia', 'easteurope', 'europe', 'oceania']
    #continents = ['africa', 'namerica', 'camerica', 'samerica', 'russia', 'easteurope', 'europe', 'oceania']
    continents = ['namerica', 'europe']

    indir = '{:s}/Maps-Product/World-Final/'.format(dir_data)

    for continent in continents:
    
        fileValide   = '{:s}WII-{:s}-valide.geojson'.format(indir,continent)
        fileValideld = '{:s}WII-{:s}-valide.ldgeojson.ld'.format(indir,continent)

        recipe = {}
        recipe['version'] = 1
        recipe['layers']  = {
                             'wii-{:s}'.format(continent):{
                                                           'source':"mapbox://tileset-source/ronan-p33/wii-{:s}".format(continent), 
                                                           'minzoom': 6,
                                                           'maxzoom': 10,
                                                           } 
                             }
       
        with open('{:s}recipe-wii-{:s}.json'.format(indir,continent), 'w') as fp:
            json.dump(recipe, fp)

        lines.append('ogr2ogr -f GeoJSONSeq {:s} {:s}\n'.format(fileValideld, fileValide) )
        lines.append('tilesets upload-source ronan-p33 wii-{:s} {:s}\n'.format(continent, fileValideld))
        lines.append('tilesets create ronan-p33.wii-{:s} --recipe {:s}recipe-wii-{:s}.json --name "wii {:s}"\n'.format(continent,indir,continent, continent))
        lines.append('tilesets publish ronan-p33.wii-{:s}\n'.format(continent))

        lines.append('\n')
 
    with open('run_push2Mapbox.sh', 'w') as fp:
        fp.writelines(lines)
    
