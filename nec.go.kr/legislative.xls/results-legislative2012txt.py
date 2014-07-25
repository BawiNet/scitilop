# -- coding: utf-8 --
#!python

import os
import sys

area_code = dict()
area_code['서울'] = 11
area_code['부산'] = 21
area_code['대구'] = 22
area_code['인천'] = 23
area_code['광주'] = 24
area_code['대전'] = 25
area_code['울산'] = 26
area_code['세종'] = 29
area_code['경기'] = 31
area_code['강원'] = 32
area_code['충남'] = 33
area_code['충북'] = 34
area_code['전북'] = 35
area_code['전남'] = 36
area_code['경북'] = 37
area_code['경남'] = 38
area_code['제주'] = 39

f_out = dict()
dirname_txt = '2012.txt'
for filename in os.listdir(dirname_txt):
    if( not filename.endswith('.xls.txt') ):
        continue
    town_name = filename.split('_')[1]
    filename_out = 'legislative2012.%s.txt'%area_code[town_name]
    if( not f_out.has_key(filename_out) ):
        f_out[filename_out] = open(filename_out,'w')
    sys.stderr.write(filename+' -> '+filename_out+'\n')
    
    tmp_loc = 0
    candidate_list = []
    f = open(os.path.join(dirname_txt,filename),'r')
    for line in f:
        if( line.startswith('투표수') ):
            tmp_loc = 1
            continue
        if( line.startswith('합계') ):
            tmp_loc = 2
            continue
        if( tmp_loc == 0 ):
            continue
        elif( tmp_loc == 1 ):
            candidate_list += line.strip().split()

    print candidate_list
    f.close()

for tmp_f in f_out.values():
    tmp_f.close()
