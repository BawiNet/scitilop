#!/usr/bin/env python

import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs

db = SqliteDatabase( "db/area_info.sqlite3")

class area_info( Model ):
	id = IntegerField()
	sig_lvl = CharField()
	sig_cd = CharField()
	sig_nm = CharField()
	geoJSON = TextField()
	parent_id = IntegerField()
	
	class Meta:
		database = db

properties_template = string.Template( '{"sig_nm": "$sig_nm","sig_cd": "$sig_cd", "sig_lvl1" : "$sig_lvl1", "sig_lvl2" : "$sig_lvl2" }' )
features = []

for area in area_info.select().where( area_info.sig_lvl == 3):
    feature = {}
    feature['type'] = "Feature"
    feature['geometry'] = json.loads( area.geoJSON )

    for lvl2 in area_info.select().where( area_info.sig_cd == area.sig_cd[:5] ):
        lvl2_name = lvl2.sig_nm

    for lvl1 in area_info.select().where( area_info.sig_cd == area.sig_cd[:2] ):
        lvl1_name = lvl1.sig_nm
        
    feature['properties'] = { "sig_nm": area.sig_nm, "sig_cd": area.sig_cd, "sig_lvl1": lvl1_name, "sig_lvl2": lvl2_name  }
    features.append( feature )


# dummy values
features.append( {  "geometry": 
                        {"type": "MultiPolygon",
                         "coordinates": [[[[36.207213,37.443708],[36.618674,37.341285],[36.361791,36.862807],[36.182326,37.036289],[36.207213,37.443708]]],[[[36.448681,37.493008],[36.593944,37.624014],[36.670508,37.495472],[36.640165,37.448815],[36.448681,37.493008]]]]},
                         "type": "Feature",
                         "properties": {"sig_nm": "dummy1","sig_cd": "9999999", "sig_lvl1": "dummy1", "sig_lvl2":"dummy1" }
                 } 
                )
features.append( {  "geometry": 
                       {"type": "MultiPolygon","coordinates": [[[[34.702075,36.219219],[34.937832,36.086951],[34.611321,35.885996],[34.292952,36.04197],[34.702075,36.219219]]],[[[34.968326,35.898573],[35.197403,36.021408],[35.216241,35.843566],[35.067838,35.80399],[34.968326,35.898573]]]]},
                        "type": "Feature",
                        "properties": {"sig_nm": "dummy2","sig_cd": "9999998", "sig_lvl1":"dummy2", "sig_lvl2":"dummy2" }
                } 
              )
	
sgg = { "type" : "FeatureCollection"
    }
sgg['features'] = features

print sgg.keys()

geoJSON = json.dumps( sgg, separators = (',', ':') ) + ";"

f = codecs.open("generated.geojson", encoding='utf-8', mode='w')
f.write ( geoJSON )
f.close()

#print geoJSON
#for area in area_info.select().join(area_info).wherewhere(area_info.sig_lvl == '3', area_info.parent_id == 7675 ):

#for area in area_info.select().where(area_info.sig_lvl == '3', area_info.parent_id == 7675 ):
#	print area.sig_lvl, area.sig_cd, area.sig_nm

db.close()


