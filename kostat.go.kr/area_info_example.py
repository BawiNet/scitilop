#!/usr/bin/env python

import json
import os
import mysql.connector
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs

db = MySQLDatabase( user='root', password='2volutio',
                              host='127.0.0.1',
                              database='election_info' )

class area_info( Model ):
	id = IntegerField()
	sig_lvl = CharField()
	sig_cd = CharField()
	sig_nm = CharField()
	geoJSON = TextField()
	parent_id = IntegerField()
	
	class Meta:
		database = db

properties_template = string.Template( '{"TL_SCCO_1": "$sig_nm","sig_eng_nm": "#","area": 0,"gid": 0,"sig_cd": "$sig_cd","TL_SCCO_SI": "#"}' )
features = []

for area in area_info.select().where( area_info.sig_lvl == 1 ):
	feature = {}
	feature['type'] = "Feature"
	feature['geometry'] = json.loads( area.geoJSON )
	feature['properties'] = { "TL_SCCO_1": area.sig_nm, "sig_eng_nm":"#", "area": 0, "gid": 0 , "sig_cd": area.sig_cd, "TL_SCCO_SI":"#" }
	features.append( feature )

for area in area_info.select().where( area_info.sig_cd << [ '31070', '31012', '31013', '31014', '31230' ] ):
	print area.sig_nm, area.sig_cd
	feature = {}
	feature['type'] = "Feature"
	feature['geometry'] = json.loads( area.geoJSON )
	feature['properties'] = { "TL_SCCO_1": area.sig_nm, "sig_eng_nm":"#", "area": 0, "gid": 0 , "sig_cd": area.sig_cd, "TL_SCCO_SI":"#" }
	features.append( feature )


#features.append( {"geometry": {"type": "MultiPolygon","coordinates": [[[[36.207213,37.443708],[36.618674,37.341285],[36.361791,36.862807],[36.182326,37.036289],[36.207213,37.443708]]],[[[36.448681,37.493008],[36.593944,37.624014],[36.670508,37.495472],[36.640165,37.448815],[36.448681,37.493008]]]]},"type": "Feature","properties": {"TL_SCCO_1": "#","sig_eng_nm": "dummy1","area": 1,"gid": 0,"sig_cd": "99999","TL_SCCO_SI": "#"}} )
#features.append( {"geometry": {"type": "MultiPolygon","coordinates": [[[[34.702075,36.219219],[34.937832,36.086951],[34.611321,35.885996],[34.292952,36.04197],[34.702075,36.219219]]],[[[34.968326,35.898573],[35.197403,36.021408],[35.216241,35.843566],[35.067838,35.80399],[34.968326,35.898573]]]]},"type": "Feature","properties": {"TL_SCCO_1": "#","sig_eng_nm": "dummy2","area": 1112,"gid": 1,"sig_cd": "99998","TL_SCCO_SI":"#"}} )
	
sgg = {	"crs": 
						{	"type":"name", 
							"properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
						},
				"type": "FeatureCollection" 
			} 
sgg['features'] = features

print sgg.keys()

geoJSON = "var sgg = " + json.dumps( sgg, separators = (',', ':') ) + ";"

f = codecs.open("../sgg_test.geojson", encoding='utf-8', mode='w')
f.write ( geoJSON )
f.close()

#print geoJSON
#for area in area_info.select().join(area_info).wherewhere(area_info.sig_lvl == '3', area_info.parent_id == 7675 ):

#for area in area_info.select().where(area_info.sig_lvl == '3', area_info.parent_id == 7675 ):
#	print area.sig_lvl, area.sig_cd, area.sig_nm

db.close()


