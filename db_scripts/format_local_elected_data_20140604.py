#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import json
import os
import sys
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs
import os.path
from election_class import *
import time
import yaml
import os.path

import urllib2
from bs4 import BeautifulSoup

''' 2014-06-04 지방선거 당선자 정보 URL 형식
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%233&electionCode=3&cityCode=-1&sggCityCode=0&townCode=-1&sggTownCode=0&x=16&y=14
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%234&electionCode=4&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=37&y=17
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%235&electionCode=5&cityCode=1100&sggCityCode=0&townCode=1101&sggTownCode=0&x=42&y=2
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%236&electionCode=6&cityCode=1100&sggCityCode=0&townCode=1101&sggTownCode=0&x=50&y=13
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%238&electionCode=8&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=46&y=9
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%239&electionCode=9&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=42&y=10
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%2310&electionCode=10&cityCode=4900&sggCityCode=0&townCode=-1&sggTownCode=0&x=40&y=10
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%2311&electionCode=11&cityCode=-1&sggCityCode=0&townCode=-1&sggTownCode=0&x=41&y=10
'''

from string import Template
url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fep%2Fepei01.jsp&topMenuId=EP&secondMenuId=EPEI01&menuId=&statementId=EPEI01_%23${electioncode}&electionCode=${electioncode}&cityCode=${citycode}&sggCityCode=${sggcitycode}&townCode=${towncode}&sggTownCode=${sggtowncode}&x=16&y=14'
elec_type_hash = {
#	'1': u"대통령선거",
#	'2': u"국회의원선거",
	'3': u"시·도지사선거",
	'4': u"구·시·군의 장선거",
	'5': u"시·도의회의원선거",
	'6': u"구·시·군의회의원선거",
	'8': u"광역의원비례대표선거",
	'9': u"기초의원비례대표선거",
	'10': u"교육의원선거",
	'11': u"교육감선거"
}

def get_htmldata( electioncode, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = "", local_only = False ):
	
	filename = "htmldata/elected_2014-06-04_" + electioncode + "_" + citycode + "_" + sggcitycode + "_" + towncode + "_" + sggtowncode + ".html"
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

def process_elected_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata ):

	return_object = {}

	html = BeautifulSoup( htmldata )
	table = html.find( id='table01' )
	if table == None:
		return return_object
	else:
		
		tbody = table.tbody
		for tr in tbody.find_all( 'tr' ):
			td_list = tr.find_all( 'td' )
			if elec_type in ['3', '4']:
				elec_nm_idx = 0
				party_nm_idx = 1
				name_idx = 3
				sex_idx = 4
				birthdate_idx = 5
				vote_count_idx = 10
			elif elec_type in [ '5', '6' ]:
				elec_nm_idx = 1
				party_nm_idx = 2
				name_idx = 4
				sex_idx = 5
				birthdate_idx = 6
				vote_count_idx = 11
			elif elec_type in [ '8' ]:
				elec_nm_idx = 0
				party_nm_idx = 1
				name_idx = 4
				sex_idx = 5
				birthdate_idx = 6
				vote_count_idx = -1
			elif elec_type in [ '9' ]:
				elec_nm_idx = 0
				party_nm_idx = 2
				name_idx = 5
				sex_idx = 6
				birthdate_idx = 7
				vote_count_idx = -1
			elif elec_type in [ '10', '11' ]:
				elec_nm_idx = 0
				name_idx = 2
				sex_idx = 3
				birthdate_idx = 4
				vote_count_idx = 9

			elec_area_nm = td_list[elec_nm_idx].contents[0].replace( ' ','')
			if elec_type in [ '5', '6' ]:
				elec_cd_prefix = elec_type + towncode + '%'
			else:
				elec_cd_prefix = elec_type + citycode[0:2] + '%'

			ea = elec_area_info()
			if elec_type in [ '3','8','11']:
				try:
					ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_area_nm.encode( 'utf-8') ) & ( elec_area_info.elec_lvl == elec_type ))
				except elec_area_info.DoesNotExist:
					print "no such elec_area", elec_area_nm
			else:
				try:
					ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_area_nm.encode( 'utf-8') ) & ( elec_area_info.elec_cd % elec_cd_prefix ) & ( elec_area_info.elec_lvl == elec_type ))
				except elec_area_info.DoesNotExist:
					print "no such elec_area", elec_area_nm, elec_cd_prefix

			if elec_type in [ '10', '11' ]:
				party_nm = ""
				party_id = None
			else:
				party_nm = td_list[party_nm_idx].contents[0].strip()
			name_array = td_list[name_idx].contents
			#print name_array
			name = name_array[0].strip()
			#print name_array[2]
			#hanja = name_array[2][1:-1]
			sex = td_list[sex_idx].contents[0]
			if sex == u'남':
				sex = 'M'
			else:
				sex = 'F'
			y, m, d = td_list[birthdate_idx].contents[0].strip().split( '/' )
			birthdate= str( date( int( y ), int( m ), int( d ) ) )
			#print elec_area_nm, candidate_num, party_nm, name, sex, birthdate #unicode( hanja ), sex, birthdate
			vote_count = 0
			vote_ratio = 0.0
			if vote_count_idx >= 0:
				vote_count_data = td_list[vote_count_idx]
				if vote_count_data.contents[0] == u'무투표당선':
					#print "==", vote_count_data
					pass
				else:
					#print "!=", vote_count_data
					vote_count = vote_count_data.contents[0].replace(',','')
					vote_ratio = vote_count_data.contents[2][1:-1]

			elected_data = { 'name': name, 'birthdate': birthdate, 'vote_count': vote_count, 'vote_ratio': vote_ratio }
			if ea.elec_cd not in return_object.keys():
				return_object[ea.elec_cd] = {}
				return_object[ea.elec_cd]['elected_list'] = []
				return_object[ea.elec_cd]['elec_cd'] = ea.elec_cd
				return_object[ea.elec_cd]['elec_nm'] = ea.elec_nm
			return_object[ea.elec_cd]['elected_list'].append( elected_data )
	return return_object

import argparse
from argparse import RawTextHelpFormatter

prog_desc = u'2014년 6월 4일 지방선거 당선자 정보 가져오기'
parser = argparse.ArgumentParser(description=prog_desc, formatter_class=RawTextHelpFormatter)

sido_help_msg = u'광역시/도 코드.\n11: 서울 21: 부산 22: 대구 23: 인천 24: 광주 25: 대전\n26: 울산 29: 세종시 31: 경기 32: 강원 33: 충북 34: 충남\n35: 전북 36: 전남 37: 경북 38: 경남 39: 제주'

parser.add_argument('command', nargs='?', help='작업종류. C: Crawling, F: Formatting.')

args = parser.parse_args()
print args.command

work_mode = args.command

if work_mode == 'C':
	local_only = False
	work_type = "Crawling"
else:
	work_type = "Formatting"
	local_only = True

log_str = ""
elec_date = "2014-06-04"

elec_type_list = elec_type_hash.keys()
elec_type_list.sort()

elected_data_hash = {}
elected_data_hash[elec_date] = {}


noresult_keyword = "검색된 결과가 없습니다."
'''
3&electionCode=3&cityCode=-1&sggCityCode=0&townCode=-1&sggTownCode=0&x=16&y=14
4&electionCode=4&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=37&y=17
5&electionCode=5&cityCode=1100&sggCityCode=0&townCode=1101&sggTownCode=0&x=42&y=2
6&electionCode=6&cityCode=1100&sggCityCode=0&townCode=1101&sggTownCode=0&x=50&y=13
8&electionCode=8&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=46&y=9
9&electionCode=9&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=42&y=10
10&electionCode=10&cityCode=4900&sggCityCode=0&townCode=-1&sggTownCode=0&x=40&y=10
11&electionCode=11&cityCode=-1&sggCityCode=0&townCode=-1&sggTownCode=0&x=41&y=10
'''
for elec_type in elec_type_list:
	elected_data_hash[elec_date][elec_type] = {}
	print "\n", work_type, elec_type, elec_type_hash[elec_type], "data:"

	area_list = []
	if elec_type == '10': #교육의원. 제주특별자치도 제주시 1, 2, 3 서귀포시 4, 5 선거구. 
		area = area_info.get_area_by_cd( '39', elec_date )
		area_list = [ area ]
	elif elec_type in [ '3', '11' ]:
		pass
	else:
		if elec_type in [ '5', '6' ]:
			sig_lvl = 2
			area_select = area_info.select().where( ( area_info.sig_lvl == sig_lvl ) & ( area_info.valid_from <= elec_date ) & ( area_info.valid_to >= elec_date ) & ( area_info.nec_cd != None ) & ( area_info.spcity_cd != '1' ) )
		else:
			sig_lvl = 1
			area_select = area_info.select().where( ( area_info.sig_lvl == sig_lvl ) & ( area_info.valid_from <= elec_date ) & ( area_info.valid_to >= elec_date ) & ( area_info.nec_cd != None ) )
		area_list = [ area for area in area_select ]
		print "total", len( area_list ), "areas."

	#print "a"

	if len( area_list ) == 0:
		citycode = '-1'
		sggcitycode = '0'
		towncode = '-1'
		sggtowncode = '0'

		sys.stdout.write('.')
		#print elec_type, citycode, sggcitycode, towncode, sggtowncode
		htmldata = get_htmldata( elec_type, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = noresult_keyword, local_only = local_only )
		if htmldata == "":
			#print "no data for", elec_type, towncode, sggtowncode, i
			#max_sgg_num[elec_type][towncode] = i - 1
			continue
		if work_mode == 'F':
			result_hash = process_elected_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata )
			for key in result_hash.keys():
				elected_data_hash[elec_date][elec_type][key] = result_hash[key]

	else:

		for area in area_list:
			#if elec_type == '6' and area.nec_cd == '4302':
				#print elec_type, area.sig_cd, area.sig_nm, area.nec_cd
			citycode = area.nec_cd[0:2] + '00'
			sggcitycode = '0'
			towncode = '-1'
			sggtowncode = '0'

			if elec_type in [ '5', '6' ]:
				towncode = area.nec_cd

			sys.stdout.write('.')

			#print elec_type, citycode, sggcitycode, towncode, sggtowncode
			htmldata = get_htmldata( elec_type, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = noresult_keyword, local_only = local_only)
			if htmldata == "":
				#print "no data for", elec_type, towncode, sggtowncode, i
				#max_sgg_num[elec_type][towncode] = i - 1
				break

			if work_mode == 'F':
				result_hash = process_elected_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata )
				#elected_list = result_hash['candidate_list']
				#print len( candidate_list ), len( elec_area_list )
				for key in result_hash.keys():
					elected_data_hash[elec_date][elec_type][key] = result_hash[key]


if work_mode == 'F':
	elected_data_json = json.dumps( elected_data_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )
	f = codecs.open("elected_data_2014-06-04.json", encoding='utf-8', mode='w')
	f.write ( elected_data_json )
	f.close()