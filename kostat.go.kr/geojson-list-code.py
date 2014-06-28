#!/usr/bin/env python
import os
import sys
import string
import urllib
import json
import time
import gzip
from pprint import pprint

filename_geojson = sys.argv[1]

json_data = open(filename_geojson,'r')
if( filename_geojson.endswith('gz') ):
    json_data = gzip.open(filename_geojson,'rb')

data = json.load(json_data)
for tmp in data['features']:
    #print tmp.keys(), tmp['properties'].keys()
    if( tmp['properties'].has_key('Name') ):
        tmp_code = tmp['properties']['Name']
    elif( tmp['properties'].has_key('admcode') ):
        tmp_code = tmp['properties']['admcode']
    
    if( tmp['properties'].has_key('Description') ):
        tmp_unit_name = tmp['properties']['Description']
    elif( tmp['properties'].has_key('admname') ):
        tmp_unit_name = tmp['properties']['admname']
    print tmp_code.encode('utf-8')+"\t"+tmp_unit_name.encode('utf-8')
json_data.close()
