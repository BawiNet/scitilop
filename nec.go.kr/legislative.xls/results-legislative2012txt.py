# -- coding: utf-8 --
#!python

import os
import sys

area_code = dict()
area_code['����'] = 11
area_code['�λ�'] = 21
area_code['�뱸'] = 22
area_code['��õ'] = 23
area_code['����'] = 24
area_code['����'] = 25
area_code['���'] = 26
area_code['����'] = 29
area_code['���'] = 31
area_code['����'] = 32
area_code['�泲'] = 33
area_code['���'] = 34
area_code['����'] = 35
area_code['����'] = 36
area_code['���'] = 37
area_code['�泲'] = 38
area_code['����'] = 39

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
        if( line.startswith('��ǥ��') ):
            tmp_loc = 1
            continue
        if( line.startswith('�հ�') ):
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
