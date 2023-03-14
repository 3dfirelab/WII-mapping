import geopandas as gpd

#homebrewed
import tools

if __name__ == '__main__':
    
    continent = 'asia'

    indir = '/mnt/dataEstrella/WII/FuelCategories-CLC/{:s}'.format(continent)
    ptdx = 100
    dbox = 1000.

    idxclc = range(1,6)
    for iv in idxclc:
        print('fuel cat {:d} ... '.format(iv) )
        fuelCat = gpd.read_file(indir+'fuelCategory{:d}.geojson'.format(iv))

        fuelCat = tools.add_AI2gdf(fuelCat,ptdx,dbox)

        fuelCat.to_file(indir+'fuelCategory{:d}.geojson'.format(iv), driver='GeoJSON')

    print ('done')
