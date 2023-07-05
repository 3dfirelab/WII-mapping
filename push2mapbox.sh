#!/bin/bash
#
set -x
export YOUR_MAPBOX_ACCESS_TOKEN=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg

#export dirin="/mnt/dataEuropa/WII/Maps-Product/World-Final/"
#cd $dirin
export geojsonNameFile=$1
export tilesetNAme=$2

#to get aws key
export info=`curl -X POST "https://api.mapbox.com/uploads/v1/ronan-p33/credentials?access_token="$YOUR_MAPBOX_ACCESS_TOKEN`


export AWS_ACCESS_KEY_ID=`echo $info | jq -r '.accessKeyId'`
export AWS_SECRET_ACCESS_KEY=`echo $info | jq -r '.secretAccessKey'`
export AWS_SESSION_TOKEN=`echo $info | jq -r '.sessionToken'`

export AWS_BUCKET=`echo $info | jq -r '.bucket'`
export AWS_BUCKET_KEY=`echo $info | jq -r '.key'`


#convert geojson to ld
#fio cat WII-world.geojson > WII-world.ldgeojson.ld

#push to aws
aws s3 cp $geojsonNameFile s3://$AWS_BUCKET/$AWS_BUCKET_KEY

export URL="https://tilestream-tilesets-production.s3.amazonaws.com/"$AWS_BUCKET_KEY
export TILESET="ronan-p33."$tilesetNAme
export NAME=$tilesetNAme

JSON_STRING=$( jq -n \
                  --arg url_ "$URL" \
                  --arg tileset_ "$TILESET" \
                  --arg name_ "$NAME" \
                  '{url: $url_, tileset: $tileset_, name: $name_}' )

#from aws to mpabox
#url is given from above
#export curl_cmd='-X POST -H "Content-Type: application/json" -H "Cache-Control: no-cache" -d' '"'$JSON_STRING'"'
export curl_cmd='-X POST -H "Content-Type: application/json" -H "Cache-Control: no-cache" -d '"'$JSON_STRING'"
echo ''
echo $curl_cmd
export curl_url=' "https://api.mapbox.com/uploads/v1/ronan-p33?access_token=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg"'
export cmd='curl '$curl_cmd$curl_url
echo $cmd
$cmd

##########
#last command is not working
##########


#test upload
#curl "https://api.mapbox.com/uploads/v1/ronan-p33/cljd1ytb10bo22kmw6np23cdw?access_token=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg"


