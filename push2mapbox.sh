#!/bin/bash
#
export YOUR_MAPBOX_ACCESS_TOKEN=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg

#to get aws key
curl -X POST "https://api.mapbox.com/uploads/v1/ronan-p33/credentials?access_token=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg"


export AWS_ACCESS_KEY_ID=ASIATNLVGLR2CQLYWFPH
export AWS_SECRET_ACCESS_KEY=s0HfPi9KUJViN5cL5qCkry80OJSk8Yc5aB45HM4h
export AWS_SESSION_TOKEN=FwoGZXIvYXdzEPD//////////wEaDJ22MqBw8+fdenNxayKYAhb8x7SjTpGUk04e5r7xYb0l3NKZjAXGGM8owU8iIxC4Tu3R1M393doweLdUE6l6V8JicWaZjHRu0KiNcIoQeQcTCE5FkMRJZjbRBTdEaSbOk9wtSoXwFyOVdpJVFfFW91IOYAhobxdIYIZYTyXDkw0tXLdXixLRjJtXxuKemJN6NYZpdm6SmrBPMlRK5kC4I+A+eKhzPD/qBn2i2IvVFDuEv1ectBFaZTkZR31I5iSTkVNcqQb0lmsFtMw17gTpr0DFjLJF3Wectr9/YFsPKQ+2AQApfzSLPGBTi8xE7xXq5XvL7LIPhEooxPGS+87z7o7dIMr3hmgh1y+9auBDLryREiTlEUQIrLVXNafNVZZIC8UNRv9fRcMo973mpAYyKdQK2uyTXadvDMtxtXLz/NSrc8RMVCN+uFmLdt+I800WLSH4ZK7gvQ7p

#convert geojson to ld
fio cat WII-world.geojson > WII-world.ldgeojson.ld

#push to aws
aws s3 cp WII-world.ldgeojson.ld s3://tilestream-tilesets-production/a1/_pending/wcupzysb7nd2l100wa96ycjlc/ronan-p33

#from aws to mpabox
#url is given from above
curl -X POST -H "Content-Type: application/json" -H "Cache-Control: no-cache" -d '{
"url": "https://tilestream-tilesets-production.s3.amazonaws.com/a1/_pending/wcupzysb7nd2l100wa96ycjlc/ronan-p33",
"tileset": "ronan-p33.wii-world"}' 'https://api.mapbox.com/uploads/v1/ronan-p33?access_token=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg'

#test upload
curl "https://api.mapbox.com/uploads/v1/ronan-p33/cljd1ytb10bo22kmw6np23cdw?access_token=sk.eyJ1Ijoicm9uYW4tcDMzIiwiYSI6ImNsamN3NWEzeDB6Nm0zZXFocHM5c2VxN2QifQ.GCF3TvmWUi-LK5KESrm5qg"


