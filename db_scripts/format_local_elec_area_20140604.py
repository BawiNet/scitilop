#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import json
import os
import sys
import mysql.connector
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs
import os.path
from election_class import *
import time
import yaml
import os.path
data_filename = "./elec_area_code_20120411.txt"
import re

import urllib2
from bs4 import BeautifulSoup

from string import Template
url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fbi%2Fbigi05.jsp&topMenuId=BI&secondMenuId=BIGI&menuId=BIGI05&statementId=BIGI05&electionCode=${electioncode}&cityCode=${citycode}&townCode=-1&x=44&y=11'
elec_type_hash = {
	'5': u"시·도의회의원선거",
	'6': u"구·시·군의회의원선거",
#	'10': u"교육의원선거",
}


def get_htmldata( electioncode, citycode, noresult_keyword = "", local_only = False ):
	
	filename = "htmldata/elec_area_info_" + electioncode + "_" + citycode
	filename += ".html"
	
	if os.path.isfile( filename ):
		f = open( filename, "r" )
		data = f.read()
		f.close()
		if noresult_keyword != "":
			#print type(data), type(noresult_keyword)
			#unidata = unicode( data )
			if data.find( noresult_keyword ) > 0:
				return ""

	else: #file not exist
		if local_only:
			return ""

		url = Template( url_template ).substitute( { 'electioncode': electioncode, 'citycode' : citycode } )
			
		data = urllib2.urlopen(url).read()
		time.sleep(3)

		if noresult_keyword != "":
			#print type(data), type(noresult_keyword)
			#unidata = unicode( data )
			if data.find( noresult_keyword ) > 0:
				return ""
		
		f = open( filename, 'w' )
		#f = codecs.open( filename, encoding='utf-8', mode='w')
		f.write ( data )
		f.close()
		
		
	return data

log_str = ""
elec_date = "2014-06-04"

#print elec_type, elec_type_hash[elec_type]
filename = 'elec_area_' + elec_date + '.json'

json_file = open( filename, 'r' )
elec_area_data_hash = json.load( json_file )
json_file.close()

elec_type_list = elec_type_hash.keys()
elec_type_list.sort()

for elec_type in elec_type_list:
	sig_lvl = 1
	if elec_type == '10': # 제주특별자치도 교육의원 선거
		area_select = area_info.select().where( ( area_info.sig_lvl == sig_lvl ) & ( area_info.valid_from < elec_date ) & ( area_info.valid_to > elec_date ) & ( area_info.nec_cd != None ) & ( area_info.sig_cd == '39' ) )
	else:
		area_select = area_info.select().where( ( area_info.sig_lvl == sig_lvl ) & ( area_info.valid_from < elec_date ) & ( area_info.valid_to > elec_date ) & ( area_info.nec_cd != None ) )
	sido_list = [ area for area in area_select ]

	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0

	for sido in sido_list:
		citycode = sido.nec_cd[0:2] + '00'
		print sido.sig_nm, elec_type, citycode
		htmldata = get_htmldata( elec_type, citycode, noresult_keyword = "검색된 결과가 없습니다.", local_only = True  )
		html = BeautifulSoup( htmldata )
		table = html.find( id='table01' )
		if table == None:
			pass
		else:
			tbody = table.tbody
			for tr in tbody.find_all( 'tr' ):
				td_list = tr.find_all( 'td' )
				sig_nm_idx = 0
				elec_nm_idx = 1
				emd_nm_idx = 2
				elect_num_idx = 3
				sig_nm = td_list[sig_nm_idx].contents[0].strip()
				elec_nm = td_list[elec_nm_idx].contents[0].strip()
				emd_nm = td_list[emd_nm_idx].contents[0].strip()
				emd_list = [ emd.strip() for emd in emd_nm.split( "," ) ]
				elect_num = td_list[elect_num_idx].contents[0].strip()
				
				try:
					
					sgg = area_info.search_by_name( sig_nm, elec_date, parent_id = sido.id, sig_lvl = '2' )
				except area_info.DoesNotExist:
					print "no such area", sig_nm, elec_date, sido.id, sig_lvl
					error_count += 1
					continue

				suba_list = []					
				for emd in emd_list:
					try:
						if emd in [ u'서둔동', u'상현2동', u'쌍용2동' ]:
							suba = area_info.search_by_name( emd, elec_date, sig_lvl = '3' )
						else:
							suba = area_info.search_by_name( emd, elec_date, parent_id = sgg.id, sig_lvl = '3' )
					except area_info.DoesNotExist:
						print "no such EMD", emd, elec_date, "in", sgg.sig_nm
						error_count += 1
						continue
					suba_list.append( suba )

				for elec_area in elec_area_data_hash[elec_date][elec_type]:
					if elec_area['elec_nm'] == elec_nm and elec_area['elec_lvl'] == elec_type and elec_area['elec_cd'][1:3] == sido.nec_cd[:2]:
						elec_area['elect_num'] = int( elect_num )
						suba_data_list = []
						for suba in suba_list:
							suba_data = { 'sig_cd': suba.sig_cd, 'sig_nm': suba.sig_nm }
							suba_data_list.append( suba_data )
						elec_area['area_list'] = suba_data_list
						#print elec_area['elec_cd'], elec_nm, elec_type
				#print sig_nm, elec_nm, emd_list, elec_num
		
		#break
			
elec_area_json = json.dumps( elec_area_data_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )

f = codecs.open("elec_area_" + elec_date + ".json", encoding='utf-8', mode='w')
f.write ( elec_area_json )
f.close()

#print max_sgg_num
	
#candidate_data_json = json.dumps( candidate_data_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )

#f = codecs.open("candidate_info.json", encoding='utf-8', mode='w')
#f.write ( candidate_data_json )
#f.close()

