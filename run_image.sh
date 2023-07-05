#!/bin/bash
#
cd src-map/
#python mapIndus.py -c europe
#python mapIndus.py -c asia

#python mapFuelCat.py -c europe
#python mapFuelCat.py -c asia

#python mapWII.py -c europe
#python mapWII.py -c asia

python mapHazardCat.py -c europe

cd ../src-analysis/
python ratioPerCountry.py -c europe
python ratioPerCountry.py -c asia




