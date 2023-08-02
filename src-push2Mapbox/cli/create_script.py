import json 

#homebrewed
sys.path.append('../../src-map/')
import tools
import params


if __name__ == '__main__':

    lines = []
    lines.append('#!/bin/bash')
    lines.append('export MAPBOX_ACCESS_TOKEN=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg')


    dir_data = tools.get_dirData()

    importlib.reload(tools)
    importlib.reload(params)
    continents = ['africa']
    #continents = ['africa', 'namerica', 'camerica', 'samerica', 'russia', 'asia', 'easteurope', 'europe', 'oceania']

    indir = '{:s}/Maps-Product/World-Final/'.format(dir_data)

    for continent in continents:
    
        fileValide   = '{:s}WII-{:s}-valide.geojson'.format(indir,continent)
        fileValideld = '{:s}WII-{:s}-valide.ldgeojson.ld'.format(indir,continent)

        recipe = {}
        recipe['version'] = 1
        recipe['layers']  = {
                             'wii-{:s}'.format(continent):{
                                                           'source':"mapbox://tileset-source/ronan-p33/wii-{:s}".format(continent) 
                                                           'minzoom': 6
                                                           'maxzoom': 10
                                                           } 
                             }
       
        with open('{:s}recipe-wii-{:s}.json'.format(indir,continent), 'w') as fp:
            json.dump(recipe, fp)

        lines.append('ogr2ogr -f GeoJSONSeq {:s} {:s}'.format(fileValideld, fileValide) )
        lines.append('tilesets upload-source ronan-p33 wii-{:s} {:s}'.format(continent, fileValideld))
        lines.append('tilesets create ronan-p33.wii-{:s} --recipe {:s}recipe-wii-{:s}.json --name "wii {:s}"'.format(continent,indir,continent, continent))
        lines.append('tilesets publish ronan-p33.wii-{:s}'.format(continent))


        
