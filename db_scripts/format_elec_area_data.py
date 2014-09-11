#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import codecs
import os.path
from election_class import *

import yaml
import os.path
data_filename = "./elec_area_code_20120411.txt"

elec_area_data = []
if os.path.isfile( data_filename  ):
    f = open( data_filename, 'r')
    elec_area_data = yaml.load(f)
    f.close()

top_area = elec_area_data[1]
del elec_area_data[1]

new_ea_list = []
for k in top_area.keys():
    ea_cd = k
    ea_nm = top_area[ea_cd]
    ea_lvl = 1
    new_ea_list.append( [ str(ea_cd), ea_lvl, ea_nm, "" ] )

for k in elec_area_data.keys():
    parent_cd = k
    for ea_cd in elec_area_data[k]:
        ea_nm = elec_area_data[k][ea_cd]
        ea_lvl = 2
        new_ea_list.append( [ str(ea_cd), ea_lvl, ea_nm, str(parent_cd) ] )

#print elec_area_data

elec_area_data_json = json.dumps( new_ea_list, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )

f = codecs.open("elec_area_info.json.", encoding='utf-8', mode='w')
#f = open("candidate_info_new.json.", mode='w')
f.write ( elec_area_data_json )
f.close()