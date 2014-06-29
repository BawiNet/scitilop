#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import gzip

filename_html = sys.argv[1]

city_code = dict()
town_code = dict()
f_code = open('city_town_code.txt','r')
for line in f_code:
    tokens = line.strip().split("\t")
    city_code[ tokens[0] ] = tokens[2].split('_')[0]
    town_code[ tokens[1] ] = tokens[2].replace('_',' ')
f_code.close()

f = open(filename_html,'r')
tmp_code = filename_html.split('.')[-2]
if( filename_html.endswith('.gz') ):
    f = gzip.open(filename_html,'rb')
    tmp_code = filename_html.split('.')[-3]
city_info = 'NA'
if( town_code.has_key(tmp_code) ):
    city_info = town_code[tmp_code]

is_thead = 0
is_tbody = 0
tr_count = 0
td_count = 0

city_name = ''
town_name = ''
unit_name = ''
info = dict()
for line in f:
    line = line.strip()

    if( line == '<thead>' ):
        is_thead = 1
    elif( line == '</thead>' ):
        is_thead = 0
    
    if( line == '<tbody>' ):
        is_tbody = 1
    elif( line == '</tbody>' ):
        is_tbody = 0

    if( is_thead + is_tbody == 0 ):
        continue
    
    if( line == '<tr>' ):
        tr_count += 1
        td_count = 0
    if( line.startswith('<td') or line.startswith('<tr')  ):
        td_count += 1

    if( line.startswith('<') ):
        continue
    if( tr_count <= 3 ):
        continue
    
    if( td_count == 2 ):
        town_name = line
        continue
    if( td_count == 3 ):
        unit_name = line
        continue
    
    if( unit_name == '소계' ):
        continue

    info_id = '%03d_%02d'%(tr_count, td_count)
    if( not info.has_key(info_id) ):
        info[info_id] = {'town':town_name, 'unit':unit_name, 'text': line }
    else:
        info[info_id]['text'] += line
f.close()

unit_id_list = list(set([x.split('_')[0] for x in info.keys()]))
for unit_id in unit_id_list:
    #  선거권이 있는 국내거소신고를 한 재외국민 및 외국인은 (재외국민수 , 외국인수)로 표기하고 본수에 포함.
    #_04: 인구수
    #_05: 확정된 선거인수, total
    #_06: 확정된 선거인수, man
    #_07: 확정된 선거인수, woman
    #_08: 부재자신고인, total
    #_09: 부재자신고인, man
    #_10: 부재자신고인, woman
    #_11: 인구대비 선거인 비율(%) 
    #_12: 세대수
    tmp_town = info['%s_04'%unit_id]['town']
    tmp_unit = info['%s_04'%unit_id]['unit']
    tmp_population = info['%s_04'%unit_id]['text'].split('(')[0].replace(',','')
    tmp_voter_man = info['%s_06'%unit_id]['text'].split('(')[0].replace(',','')
    tmp_voter_woman = info['%s_07'%unit_id]['text'].split('(')[0].replace(',','')
    tmp_remote_man = info['%s_09'%unit_id]['text'].split('(')[0].replace(',','')
    tmp_remote_woman = info['%s_10'%unit_id]['text'].split('(')[0].replace(',','')
    tmp_house = info['%s_12'%unit_id]['text'].split('(')[0].replace(',','')
    print "\t".join([city_info,tmp_town,tmp_unit,tmp_population,tmp_voter_man, tmp_voter_woman,tmp_remote_man,tmp_remote_woman,tmp_house])

    #print tmp_id,info[tmp_id]['town'],info[tmp_id]['unit'],info[tmp_id]['text']
