#!/usr/bin/env python
import os
import sys
import string
import urllib
import json
import time

f_key = open('KEY','r')
api_key = f_key.readline().strip()
f_key.close()

## latest - $key, $code, $step
query_year='2014'
query_step = 2
url_template = string.Template('http://sgis.kostat.go.kr/OpenAPI2/adminUnitBoundary.do?apikey=$key&format=geojson&code=$code&step=$step')

## old
#url_template = string.Template('http://sgis.kostat.go.kr/OpenAPI2/adminBoundaryByCYL.do?apikey=$key&format=geojson&code=$code&year=$year&level=LEVEL_00')

json_data = open('unit_boundary.2014.00.1.geojson')
data = json.load(json_data)
for tmp in data['features']:
    tmp_code = tmp['properties']['Name']
    tmp_unit_name = tmp['properties']['Description']
    tmp_var = {'key':api_key, 'code':tmp_code, 'step':query_step}

    tmp_url = url_template.substitute(tmp_var)
    sys.stderr.write('Name: %s, URL: %s\n'%(tmp_unit_name,tmp_url))

    f_url = urllib.urlopen(tmp_url)
    tmp_content = f_url.read()
    f_url.close()
    filename_out = 'unit_boundary.%s.%s.%d.geojson'%(query_year,tmp_code,query_step)
    sys.stderr.write('Write %s ... '%filename_out)
    f_out = open(filename_out,'w')
    f_out.write(tmp_content)
    f_out.close()
    sys.stderr.write('Done\n')
    time.sleep(3)
json_data.close()
