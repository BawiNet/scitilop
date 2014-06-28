#!/usr/bin/env python
import os
import sys
import string
import urllib
import json
import time
from pprint import pprint

filename_geojson = sys.argv[1]

json_data = open(filename_geojson)
data = json.load(json_data)
for tmp in data['features']:
    #print tmp.keys()
    tmp_code = tmp['properties']['Name']
    tmp_unit_name = tmp['properties']['Description']
    print "%s\t%s"%(tmp_code, tmp_unit_name)
json_data.close()
