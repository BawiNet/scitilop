#!/usr/bin/env python
# save area_info to MySQL DB

import json
import os
import mysql.connector
from datetime import date, datetime, timedelta

db = mysql.connector.connect(user='root', password='passwd',
                              host='127.0.0.1',
                              database='election_info')

add_area_info = ( "insert into area_info "
								" ( sig_lvl, sig_cd, sig_nm, valid_from, valid_to, coord_sys, geoJSON, parent_id ) "
								"  values ( %s, %s, %s, %s, %s, %s, %s, %s ) "
							)
							
rowid = {}
for dirname, dirnames, filenames in os.walk('./geojson_WGS84'):
	for filename in filenames:
		elems = filename.split( "." )
		sig_lvl = int( elems[3] )
		lvl1_cd = int( elems[2] )
		fullpath = os.path.join(dirname, filename)	
		print fullpath
		json_data = open(fullpath,'r')
		actual_data = json.load( json_data )
		json_data.close()
		cursor = db.cursor()

		for data in actual_data['features']:
			print data['properties']
			sig_cd = data['properties']['Name']
			sig_nm = data['properties']['Description']
			geoJSON = json.dumps( data['geometry'], ensure_ascii = False, separators=(',', ': ') ) 
			valid_from = date( 2014, 4, 1 )
			valid_to = date( 9999,  12, 31 )
			coord_sys = "WGS84"
			parent_id = None
			if sig_lvl == 2:
				parent_id = rowid[sig_cd[0:2]]
			elif sig_lvl == 3:
				parent_id = rowid[sig_cd[0:5]]
			cursor.execute( add_area_info, ( sig_lvl, sig_cd, sig_nm, valid_from, valid_to, coord_sys, geoJSON, parent_id ) )
			rowid[sig_cd] = cursor.lastrowid
		db.commit()

cursor.close()    
db.close()