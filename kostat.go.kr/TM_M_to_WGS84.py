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

f_key = open('KEY','r')
api_key = f_key.readline().strip()
f_key.close()




for dirname, dirnames, filenames in os.walk('./geojson'):
	for filename in filenames:
		fullpath = os.path.join(dirname, filename)	
		outpath = os.path.join( dirname + "_WGS84", filename )
		print fullpath

		if( fullpath.endswith('gz') ):
		    json_data = gzip.open(fullpath,'rb')
		else:
			json_data = open(fullpath,'r')
		actual_data = json.load( json_data )
		json_data.close()
		
		#print actual_data

		for data in actual_data['features']:
			print data['properties']
			new_polygon_list = []
			print data['geometry']['type'] 
			
			if( data['geometry']['type'] == "Polygon" ):
				data['geometry']['coordinates'] = convert_polygon_local( data['geometry']['coordinates'] )
			elif ( data['geometry']['type'] == "MultiPolygon" ):
				data['geometry']['coordinates'] = convert_multipolygon_local( data['geometry']['coordinates'] )
			
			''' old
			if( data['geometry']['type'] == "Polygon" ):
				polygon_list = data['geometry']['coordinates'] 
			elif ( data['geometry']['type'] == "MultiPolygon" ):
				polygon_list = [ p[0] for p in data['geometry']['coordinates'] ]
			
			for polygon in polygon_list:
				new_polygon = convert_polygon( api_key, polygon )
				new_polygon_list.append( new_polygon )
	
			if( data['geometry']['type'] == "Polygon" ):
				data['geometry']['coordinates'] = new_polygon_list[0]
			elif ( data['geometry']['type'] == "MultiPolygon" ):
				data['geometry']['coordinates'] = new_polygon_list
			'''
		#outpath = outpath[:-3] # remove .gz 
		sys.stderr.write('Write %s ... '%outpath)
		
		#file_str = ""

		#for k in [ "type", "features" ]:
			
		file_str = json.dumps( actual_data, ensure_ascii = False, separators=(',', ': ') ) 

		#f = codecs.open(outpath, encoding='utf-8', mode='w')
		f = gzip.open( outpath, 'wb' )
		f.write( file_str.encode( 'utf8' ) )
		f.close()

sys.stderr.write('Done\n')
sys.exit(1)
		