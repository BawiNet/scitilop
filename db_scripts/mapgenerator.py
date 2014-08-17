#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from datetime import date, datetime, timedelta
import string
import codecs

from election_class import *

import argparse
from argparse import RawTextHelpFormatter

prog_desc = u'GeoJSON 형식 시군구/읍면동 지도 파일 생성 도구'
parser = argparse.ArgumentParser(description=prog_desc, formatter_class=RawTextHelpFormatter)

sido_help_msg = u'광역시/도 코드.\n11: 서울 21: 부산 22: 대구 23: 인천 24: 광주 25: 대전\n26: 울산 29: 세종시 31: 경기 32: 강원 33: 충북 34: 충남\n35: 전북 36: 전남 37: 경북 38: 경남 39: 제주'

#parser.add_argument('date', nargs='?', help='map date')
parser.add_argument('date', help=u'YYYY-MM-DD 지도생성 기준 일자')
parser.add_argument('sido_cd', metavar='sido_cd', nargs='*', help=sido_help_msg)
parser.add_argument('-o', metavar = 'outfile', nargs='?')

args = parser.parse_args()
print args
print args.o
print args.sido_cd
print args.date
mapdate = args.date
#import sys
#sys.exit()

#print mapdate

lv1_areas = area_info.select().where( ( area_info.valid_from < mapdate ) & ( area_info.valid_to > mapdate ) & ( area_info.sig_lvl == '1' ) )
area1_list = [ area for area in lv1_areas ]
for area1 in area1_list:
	print area1.sig_cd, area1.sig_nm, area1.valid_from, area1.valid_to
area2_list = [] 
area3_list = []



if len( args.sido_cd ) > 0:
	for sido_cd in args.sido_cd:
		lv1_area = area_info.get_area_by_cd( sido_cd, mapdate )
		print lv1_area.sig_cd, lv1_area.sig_nm, lv1_area.id
		lv2_areas = area_info.select().where( ( area_info.valid_from < mapdate ) & ( area_info.valid_to > mapdate ) & ( area_info.parent_area == lv1_area.id ) )	
		lv3_areas = area_info.select().where( ( area_info.valid_from < mapdate ) & ( area_info.valid_to > mapdate ) & ( area_info.parent_area << [ area.id for area in lv2_areas ] ) )	
		for area in lv2_areas:
			print area.sig_cd, area.sig_nm
		#area2_list = [ area for area in lv2_areas ]
		area3_list.extend( [ area for area in lv3_areas ] )
		print len( area2_list ), "lv2 areas"
		print len( area3_list ), "lv3 areas"
else:
	lv3_areas = area_info.select().where( ( area_info.valid_from < mapdate ) & ( area_info.valid_to > mapdate ) & ( area_info.sig_lvl == '3' ) )
	area3_list = [ area for area in lv3_areas ]

features = []
# merge geoJSON

all_area_list = []
all_area_list.extend( area1_list )
all_area_list.extend( area2_list )
all_area_list.extend( area3_list )

for area in all_area_list:
	feature = {}
	feature['type'] = "Feature"
	geojson = area.get_boundary_geojson( mapdate ) 
	if geojson != None:
		feature['geometry'] = json.loads( geojson )
	feature['properties'] = { "TL_SCCO_1": area.sig_nm, "sig_cd": area.sig_cd  }
	features.append( feature )

sgg = {	"crs": 
						{	"type":"name", 
							"properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
						},
				"type": "FeatureCollection" 
			} 
sgg = { "type" : "FeatureCollection" }
sgg['features'] = features

#print sgg.keys()

#geoJSON = "var sgg = " + json.dumps( sgg, separators = (',', ':'), indent=0 ) + ";"
geoJSON = json.dumps( sgg, separators = (',', ':') )
json_lines = geoJSON.split( "\n" )

filename = "map_" + mapdate + ".geojson"
if args.o:
	filename = args.o
f = codecs.open( filename, encoding='utf-8', mode='w')
for line in json_lines:
	f.write ( line )
f.close()

#f = codecs.open("730_bielection_area_list.txt", encoding='utf-8', mode='w')
#f.write ( log_str)
#f.close()
