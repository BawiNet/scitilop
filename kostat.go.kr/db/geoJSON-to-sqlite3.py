#!/usr/bin/env python
# save area_info to sqlite3
import os
import sys
import gzip
import json
import sqlite3
from datetime import date, datetime, timedelta

db = sqlite3.connect('./area_info.sqlite3')
add_area_info = ( "insert into area_info "
                    " ( sig_lvl, sig_cd, sig_nm, coord_sys, geoJSON, parent_id ) "
                    "  values ( ?, ?, ?, ?, ?, ? ) ")
							
rowid = {}
for dirname, dirnames, filenames in os.walk('../geojson_WGS84'):
    for filename in filenames:
        elems = filename.split( "." )
        sig_lvl = int( elems[3] )
        lvl1_cd = int( elems[2] )
        fullpath = os.path.join(dirname, filename)    
        sys.stderr.write('Read %s\n'%fullpath)

        json_data = open(fullpath,'r')
        if( filename.endswith('.gz') ):
            json_data = gzip.open(fullpath,'rb')
        actual_data = json.load( json_data )
        json_data.close()
        cursor = db.cursor()

        for data in actual_data['features']:
            print data['properties']
            sig_cd = data['properties']['Name']
            sig_nm = data['properties']['Description']
            geoJSON = json.dumps( data['geometry'], ensure_ascii = False, separators=(',', ': ') ) 
            #valid_from = date( 2014, 4, 1 )
            #valid_to = date( 9999,  12, 31 )
            coord_sys = "WGS84"
            parent_id = None
            if sig_lvl == 2 and rowid.has_key(sig_cd[0:2]) :
                parent_id = rowid[sig_cd[0:2]]
            elif sig_lvl == 3 and rowid.has_key(sig_cd[0:5]) :
                parent_id = rowid[sig_cd[0:5]]
            #cursor.execute( add_area_info, ( sig_lvl, sig_cd, sig_nm, valid_from, valid_to, coord_sys, geoJSON, parent_id ) )
            cursor.execute( add_area_info, ( sig_lvl, sig_cd, sig_nm, coord_sys, geoJSON, parent_id ) )
            rowid[sig_cd] = cursor.lastrowid
        db.commit()

cursor.close()    
db.close()
