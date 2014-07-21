#!/usr/bin/env python

import json
import os
from datetime import date, datetime, timedelta
import string
import codecs

from election_class import *

elec = election_info.get( election_info.elec_date == '2014-07-30' )

log_str = ""
log_str += elec.elec_title + "\n"


geoJSON = {}
sig_nm = {}

for elec_area in elec_area_info.select().join( elec_elec_area_relation ).join( election_info ).where( election_info.elec_date == '2014-07-30' ):
	log_str += "\t" + elec_area.elec_cd + "\t" + elec_area.elec_nm + "\n"
	geoJSON[elec_area.elec_cd] = []
	sig_nm[elec_area.elec_cd] = elec_area.elec_nm
	
	for area in area_info.select().join( elec_area_relation ).join( elec_area_info ).where( elec_area_info.elec_cd == elec_area.elec_cd ):
		log_str += "\t\t" + area.sig_cd + "\t" + area.sig_nm + "\n"
		geoJSON[elec_area.elec_cd].append( json.loads( area.geoJSON ) )

features = []
# merge geoJSON

for area in area_info.select().where( area_info.sig_lvl == 1 ):
	feature = {}
	feature['type'] = "Feature"
	feature['geometry'] = json.loads( area.geoJSON )
	#feature['properties'] = { "TL_SCCO_1": area.sig_nm, "sig_eng_nm":"#", "area": 0, "gid": 0 , "sig_cd": area.sig_cd, "TL_SCCO_SI":"#" }
	feature['properties'] = { "TL_SCCO_1": area.sig_nm }#, "sig_eng_nm":"#", "area": 0, "gid": 0 , "sig_cd": area.sig_cd, "TL_SCCO_SI":"#" }
	#feature['properties'] = {}
	features.append( feature )

for k in geoJSON.keys():
	num_area = len( geoJSON[k] )
	new_geom = {}
	if num_area > 1:
		new_geom = { 'type':'MultiPolygon','coordinates':[]}
		for geom in geoJSON[k]:
			if geom['type'] == 'Polygon':
				new_geom['coordinates'].append( geom['coordinates'] )
			elif geom['type'] == 'MultiPolygon':
				new_geom['coordinates'].extend( geom['coordinates'] )
				
	else:
		new_geom = geoJSON[k][0]

	feature = {}
	feature['type'] = "Feature"
	feature['geometry'] = new_geom
	feature['properties'] = { "TL_SCCO_1": sig_nm[k], "sig_eng_nm":"#", "area": 0, "gid": 0 , "sig_cd": k, "TL_SCCO_SI":"#" }
	features.append( feature )



sgg = {	"crs": 
						{	"type":"name", 
							"properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
						},
				"type": "FeatureCollection" 
			} 
sgg['features'] = features

#print sgg.keys()

geoJSON = "var sgg = " + json.dumps( sgg, separators = (',', ':') ) + ";"

f = codecs.open("730byelection.geojson", encoding='utf-8', mode='w')
f.write ( geoJSON )
f.close()

#f = codecs.open("730_bielection_area_list.txt", encoding='utf-8', mode='w')
#f.write ( log_str)
#f.close()
