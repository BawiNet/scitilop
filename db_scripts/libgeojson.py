#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from datetime import date, datetime, timedelta
import string
import codecs

from election_class import *
from string import Template
import urllib2


def get_geojson_data( sig_cd, year, save = False ):
	url_template = 'http://sgis.kostat.go.kr/OpenAPI2/adminBoundaryByCYL.do?apikey=ESGA2014061055294942&format=geojson&code=${sig_cd}&year=${year}&level=LEVEL_00'
	filename = "geojson_addendum/" + sig_cd + "_" + str( year ) + ".html"
	if os.path.isfile( filename ):
		f = open( filename, "r" )
		data = f.read()
		f.close()

	else: #file not exist
		url = Template( url_template). substitute( { 'sig_cd': sig_cd, 'year' : year } )
			
		data = urllib2.urlopen(url).read()
		if len( data ) < 100:
			return ""
		if save:
			f = open( filename, 'w' )
			#f = codecs.open( filename, encoding='utf-8', mode='w')
			f.write ( data )
			f.close()
		
		
	return data

#!/usr/bin/env python
import os
import sys
import string
import urllib
import json
import time
import gzip
import codecs 

from pyproj import Proj, transform

def convert_coord_local( posX, posY ):
	latlong = Proj(proj='latlong', datum='WGS84', ellps='WGS84')
	tm = Proj(proj='tmerc', lat_0='38N', lon_0='127E', ellps='bessel', x_0=200000, y_0=500000, k=0.9999)
	newX, newY = transform(tm,latlong,posX, posY)
	return newX, newY

def convert_coord( api_key, posX, posY ):
	url_template = string.Template('http://sgis.kostat.go.kr/OpenAPI2/coordConversion.do?&apikey=$key&fromSrs=TM_M&toSrs=LL_W&posX=$posX&posY=$posY')
	tmp_var = {'key':api_key, 'posX':posX, 'posY':posY}

	convert_url = url_template.substitute(tmp_var)
	#print tmp_var
	
	ret_str = urllib.urlopen( convert_url )
	ret_json = json.load( ret_str )
	ret_str.close()
	time.sleep(0.1)

	#print ret_json

	newX = float( ret_json['posX'] )
	newY = float( ret_json['posY'] )
	return newX, newY

def convert_polygon_local( polygon ):
	linear_ring_list = polygon
	new_linear_ring_list = []
	for linear_ring in linear_ring_list:
		new_linear_ring = []
		count = 0
		for point in linear_ring:
			newX, newY = convert_coord_local( point[0], point[1] )
			new_linear_ring.append( [ newX, newY] )
			#print newX, newY
			count+=1
			#if count == 5 : break
		new_linear_ring_list.append( new_linear_ring )
	return new_linear_ring_list

def convert_multipolygon_local( multipolygon ):
	polygon_list = multipolygon
	new_multipolygon = []
	for polygon in polygon_list:
		new_polygon = convert_polygon_local( polygon )
		new_multipolygon.append( new_polygon )
	return new_multipolygon

def convert_polygon( api_key, polygon ):
	new_coords = []
	count = 0
	for point in polygon:
		newX, newY = convert_coord_local( point[0], point[1] )
		new_coords.append( [ newX, newY] )
		#print newX, newY
		count+=1
		#if count == 5 : break
	return new_coords

def find_geojson_by_cd( sig_cd, a_yy = date.today().year - 1):
	gj = get_geojson_data( sig_cd, a_yy )
	if len( data ) > 0:
		j = json.loads( data )
		if len( j['features'] ) > 0:
			#print "gotcha!", sig_cd, year
			geometry = j['features'][0]['geometry']
			if geometry['type'] == "Polygon":
				geometry['coordinates'] = convert_polygon_local( geometry['coordinates'] )
			elif ( geometry['type'] == "MultiPolygon" ):
				geometry['coordinates'] = convert_multipolygon_local( geometry['coordinates'] )
			gj_data = json.dumps( geometry, ensure_ascii = False, separators=(',', ': ') ) 
			return gj_data
	return None
