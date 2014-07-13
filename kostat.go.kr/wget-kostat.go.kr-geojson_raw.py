#!/usr/bin/env python
import os
import sys
import string
import urllib
import json
import time
import gzip

f_key = open('KEY','r')
api_key = f_key.readline().strip()
f_key.close()

## latest - $key, $code, $step
#query_year='2014'
#query_step = 2
#url_template = string.Template('http://sgis.kostat.go.kr/OpenAPI2/adminUnitBoundary.do?apikey=$key&format=geojson&code=$code&step=$step')

## old - $key, $code
query_year='1980'
query_step = 2
url_template = string.Template('http://sgis.kostat.go.kr/OpenAPI2/adminBoundaryByCYL.do?apikey=$key&format=geojson&code=$code&year=$year&level=LEVEL_00')

f_list = open('region_code.1.txt','r')
for line in f_list:
    tokens = line.strip().split("\t")
    tmp_code = tokens[0]
    if( tmp_code != '39' ):
        continue
    tmp_region_name = tokens[1]
#json_data = open('region_boundary.2014.00.1.geojson')
#data = json.load(json_data)
#for tmp in data['features']:
#    tmp_code = tmp['properties']['Name']
#    tmp_region_name = tmp['properties']['Description']

    json_2014 = gzip.open('geojson_raw/region_boundary.2014.%s.%s.geojson.gz'%(tmp_code,query_step),'rb')
    data_2014 = json.load(json_2014)
    tmp_out = {'type':'FeatureCollections','features':[]}
    filename_out = 'region_boundary.%s.%s.%d.geojson'%(query_year,tmp_code,query_step)
    for tmp in data_2014['features']:
        tmp_code2 = tmp['properties']['Name']
        tmp_region_name2 = tmp['properties']['Description']

        tmp_var = {'key':api_key, 'year':query_year, 'code':tmp_code2}
        tmp_url = url_template.substitute(tmp_var)
        sys.stderr.write("URL:%s\n"%tmp_url)

        f_url = urllib.urlopen(tmp_url)
        #tmp_content = f_url.read()
        tmp_data = json.load(f_url)
        f_url.close()
        time.sleep(3)

        tmp_out['features'] += tmp_data['features'] 

    sys.stderr.write('Write %s ... '%filename_out)
    f_out = open(filename_out,'w')
    json.dump(tmp_out, f_out)
    f_out.close()
    sys.stderr.write('Done\n')
    sys.exit(1)
#json_data.close()
