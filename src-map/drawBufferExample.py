import geopandas as gpd
from shapely.geometry import Polygon
import random
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
pmarks = []

polygon = Polygon([(0, 0), (2, 0), (2, 1), (1, 1),(1.25,2),(0,2)])
indus = gpd.GeoDataFrame({'geometry': [polygon]})


polygonv = Polygon([(3,3), (4,3.5), (4.5, 4), (3.6, 4.8), (2.8, 5.3), (2., 5), (1.8, 4,4), (2.1, 3.7)])
veg = gpd.GeoDataFrame({'geometry': [polygonv]})

veg1 = gpd.GeoDataFrame(veg.translate(-5,1)).rename({0:'geometry'}, axis='columns')
veg2 = gpd.GeoDataFrame(veg.translate(-5,-5)).rename({0:'geometry'}, axis='columns')
vegi = gpd.GeoDataFrame(veg.translate(-1,-1)).rename({0:'geometry'}, axis='columns')

veg = pd.concat([vegi, veg1, veg2]) 

fig = plt.figure()
ax = plt.subplot(111)
indus.plot(ax=ax, color='tab:blue')
pmarks.append(Patch(facecolor='tab:blue', label='industry'))
veg.plot(ax=ax, color='tab:green', alpha=0.5)
pmarks.append(Patch(facecolor='tab:green', label='vegetation'))

indus_ = indus.copy()
indus_['geometry'] = indus_.geometry.apply(lambda g: g.buffer(1.5))

indus_.plot(ax=ax, color='none', edgecolor='k' ,label='buffer', legend=True)
pmarks.append(Patch(facecolor='none', edgecolor='k',label='buffer'))

wii = gpd.overlay(veg, indus_, how = 'intersection', keep_geom_type=False)
wii.plot(ax=ax,  color='None', edgecolor='tab:orange', hatch="//", label='wii', legend=True)
pmarks.append(Patch(facecolor='none', edgecolor='tab:orange',hatch="//", label='WII'))

handles, _ = ax.get_legend_handles_labels()
ax.legend(handles=[*handles,*pmarks], loc='upper right')

ax.set_axis_off()

fig.savefig('bufferExample.png')
plt.close(fig)

plt.show()


