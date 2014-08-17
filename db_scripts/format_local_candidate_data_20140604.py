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


import urllib2
from bs4 import BeautifulSoup

from string import Template
url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%23${electioncode}&electionCode=${electioncode}&cityCode=${citycode}&sggCityCode=${sggcitycode}&townCode=${towncode}&sggTownCode=${sggtowncode}&x=38&y=15'

elec_type_hash = {
#	'1': u"대통령선거",
#	'2': u"국회의원선거",
	'3': u"시·도지사선거",
	'4': u"구·시·군의 장선거",
	'5': u"시·도의회의원선거",
	'6': u"구·시·군의회의원선거",
	'8': u"광역의원비례대표선거",
	'9': u"기초의원비례대표선거",
#	'10': u"교육의원선거",
	'11': u"교육감선거"
}


def get_htmldata( electioncode, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = "", local_only = False ):
	
	filename = "htmldata/" + electioncode + "_" + citycode
	if sggcitycode != '-1':
		filename += "_" + sggcitycode
	if sggtowncode != '0':
		filename += "_" + sggtowncode
	filename += ".html"
	#print filename
	
	if os.path.isfile( filename ):
		f = open( filename, "r" )
		data = f.read()
		f.close()

	else: #file not exist
		if local_only:
			return ""
		url = Template( url_template ).substitute( { 'electioncode': electioncode, 'citycode' : citycode, 'sggcitycode': sggcitycode, 'towncode': towncode, 'sggtowncode': sggtowncode } )
			
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



def process_candidate_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata ):
		html = BeautifulSoup( htmldata )
		table = html.find( id='table01' )
		tbody = table.tbody
		for tr in tbody.find_all( 'tr' ):
			td_list = tr.find_all( 'td' )
			if elec_type == '11':
				area_idx = 0
				#candnum_idx = 2
				#party_idx = 3
				name_idx = 2
				sex_idx = 3
				birthday_idx = 4
				candidate_num = ""
				party_nm = ""
			elif elec_type in [ '8', '9' ]:
				area_idx = 0
				party_idx = 2
				candnum_idx = 3
				name_idx = 4
				sex_idx = 5
				birthday_idx = 6
			else:
				area_idx = 0
				candnum_idx = 2
				party_idx = 3
				name_idx = 4
				sex_idx = 5
				birthday_idx = 6
						
			area_nm = td_list[area_idx].contents[0]
			if elec_type != '11':
				party_nm = td_list[party_idx].contents[0].strip()
				if elec_type in [ '8','9']:
					
					candidate_num = td_list[party_idx].contents[2].strip().replace('(','').replace(')','') + "-" + td_list[candnum_idx].contents[0].strip()
				else:
					if len( td_list[candnum_idx].contents ) > 0:
						candidate_num = td_list[candnum_idx].contents[0].strip()
					else:
						candidate_num = ""
					#party_nm = td_list[party_idx].contents[0].strip()
				
			name_array = td_list[name_idx].contents
			name = name_array[0].strip()
			hanja = name_array[2][1:-1]
			sex = td_list[sex_idx].contents[0]
			if sex == u'남':
				sex = 'M'
			else:
				sex = 'F'
			y, m, d = td_list[birthday_idx].contents[0].split( '/' )
			birthdate= str( date( int( y ), int( m ), int( d ) ) )
			#print area_nm, candidate_num, party_nm, name, sex, birthdate #unicode( hanja ), sex, birthdate
			try:
				person_info.get( ( person_info.name == name ) & ( person_info.sex == sex ) & ( person_info.birthdate == birthdate ) )
			except person_info.DoesNotExist:
				print "no such person", name, sex, birthdate
				person = person_info()
				person.name = name
				person.birthdate = birthdate
				person.sex = sex
				person.hanja = hanja
				person.save()

			if party_nm != '':
				try:
					party_info.get( ( ( party_info.party_nm == party_nm ) | ( party_info.short_nm == party_nm ) ) & (party_info.valid_from <= elec_date ) & ( party_info.valid_to >= elec_date ) )
				except party_info.DoesNotExist:
					print "no such party", party_nm 
					party = party_info()
					party.party_nm = party_nm
					party.valid_from = elec_date
					party.valid_to = '9999-12-31'
					party.save()
					#party_hash[party_nm] = [ elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode ]
			
			
			return
			#ea = elec_area_info.get( 
			
			#try:
			#	candidate_info.

def make_elec_area_cd( elec_type, nec_cd ):
	if elec_type in [ '3', '8', '11' ] : # 광역시도 단위
		return nec_cd + "00"
	elif elec_type in [ '4', '9' ] : # 시군구 단위
		return elec_type + nec_cd + "00"
	elif elec_type in [ '5', '6', '10' ]: #시군구 하위
		return elec_type + nec_cd # + 1, 2 or 가, 나 선거구 (01, 02, ...)

log_str = ""
elec_date = "2014-06-04"
elec_type = "3"

max_sgg_num = { '5':{}, '6':{} }
#print elec_type, elec_type_hash[elec_type]

elec_type_list = elec_type_hash.keys()
elec_type_list.sort()

candidate_data_hash = {}
candidate_data_hash[elec_date] = {}
party_hash = {}
#candidate_data_hash[elec_date] = {}
#print "0"

for elec_type in elec_type_list:
	if elec_type in [ '3','8','11' ]:
		sig_lvl = 1
	else:
		sig_lvl = 2
	area_select = area_info.select().where( ( area_info.sig_lvl == sig_lvl ) & ( area_info.valid_from < elec_date ) & ( area_info.valid_to > elec_date ) & ( area_info.nec_cd != None ) )
	area_list = [ area for area in area_select ]

#	print "a"

	for area in area_list:

#		print "b"

		elec_area_cd = make_elec_area_cd( elec_type, area.nec_cd )
		#print elec_type, area.id, area.sig_nm, area.sig_cd, eacd
		#print elec_type, elec_type_hash[elec_type], area.sig_cd, area.sig_nm, elec_area_cd

		sggcitycode = '-1'
		towncode = '-1'
		sggtowncode = '0'

		citycode = area.nec_cd[0:2] + '00'
		if elec_type in [ '4', '9', '10' ]:
			sggcitycode = elec_area_cd

		if elec_type in [ '5', '6' ]:
			towncode = area.nec_cd
			sggtowncode = elec_area_cd

			for i in range(1, 15):
				sggtowncode = elec_area_cd + '{:02d}'.format( i )
				htmldata = get_htmldata( elec_type, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = "검색된 결과가 없습니다.", local_only = True )
				
				if htmldata == "":
					#print "no data for", elec_type, towncode, sggtowncode, i
					#max_sgg_num[elec_type][towncode] = i - 1
					break
				
				process_candidate_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata )
				
		else:
			htmldata = get_htmldata( elec_type, citycode, sggcitycode, towncode, sggtowncode, local_only = True )
			process_candidate_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata )
		#break

		

for party in party_hash.keys():
	print "[", party, "]"
#print max_sgg_num
	
#candidate_data_json = json.dumps( candidate_data_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )

#f = codecs.open("candidate_info.json", encoding='utf-8', mode='w')
#f.write ( candidate_data_json )
#f.close()

