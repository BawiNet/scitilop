#!/usr/bin/env python
import os
import sys


city_name2code = dict()
f_city = open('city_code.raw','r')
for line in f_city:
    tokens = line.strip().split()
    tmp_code = tokens[0].strip()
    tmp_name = tokens[1].strip()
    city_name2code[tmp_name] = tmp_code
f_city.close()

current_city_code = 'NA'
current_city_name = 'NA'
f_town = open('town_code.raw','r')
for line in f_town:
    tmp_line = line.strip()
    if( tmp_line == '' ):
        continue
    if( city_name2code.has_key(tmp_line) ):
        current_city_name = tmp_line
        current_city_code = city_name2code[tmp_line]
        continue
    tmp_tokens = tmp_line.split('>')
    tmp_code = tmp_tokens[0].strip().replace('<option value=','').replace('"','').replace('selected=selected','')
    tmp_name = tmp_tokens[1].strip().replace('</option','').replace('>','')
    print "%s\t%s\t%s_%s"%(current_city_code,tmp_code,current_city_name,tmp_name)
f_town.close()
