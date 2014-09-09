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

''' 2014-06-04 지방선거 후보자 정보 URL 형식
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%233&electionCode=3&  	cityCode=1100           31100 4110100 5110101 6110101 81100 9110100 10490101 111100
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%234&electionCode=4&  	cityCode=1100		sggCityCode=4110100		townCode=			sggTownCode=0
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%235&electionCode=5&  	cityCode=1100		sggCityCode=					townCode=1101	sggTownCode=5110101
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%236&electionCode=6&  	cityCode=1100		sggCityCode=					townCode=1101	sggTownCode=6110101
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%238&electionCode=8&  	cityCode=1100		sggCityCode=					townCode=			sggTownCode=0
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%239&electionCode=9&  	cityCode=1100		sggCityCode=9110100		townCode=			sggTownCode=0
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%2310&electionCode=10&	cityCode=4900		sggCityCode=10490101	townCode=			sggTownCode=0
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%2311&electionCode=11&	cityCode=1100		sggCityCode=					townCode=			sggTownCode=0
'''

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
	'10': u"교육의원선거",
	'11': u"교육감선거"
}

def get_htmldata( electioncode, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = "", local_only = False ):
	
	filename = "htmldata/candidate_2014-06-04_" + electioncode + "_" + citycode + "_" + sggcitycode + "_" + towncode + "_" + sggtowncode + ".html"
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

def find_max_elec_area_num( elec_type, htmldata ):
	html = BeautifulSoup( htmldata )
	if elec_type in [ '5', '6' ]:
		select_control = html.find( id='sggTownCode' )
	elif elec_type == '10':
		select_control = html.find( id='sggCityCode' )

	if select_control != None:
		option_list = select_control.find_all( 'option' )
		elec_area_list = []
		for o in option_list[1:]:
			elec_cd = o['value']
			elec_nm = o.contents[0]
			#print elec_nm
			elec_area_list.append( { 'elec_cd': elec_cd, 'elec_nm': elec_nm } )
	else:
		pass
		#print "no such select"
	return len( elec_area_list )

def process_candidate_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata ):

	candidate_list = []
	elec_area_list = []
	return_object = { 'candidate_list': candidate_list, 'elec_nm': '' }

	html = BeautifulSoup( htmldata )
	table = html.find( id='table01' )
	if table == None:
		return return_object
	else:
		
		tbody = table.tbody
		for tr in tbody.find_all( 'tr' ):
			td_list = tr.find_all( 'td' )
			if elec_type in [ '10', '11' ]:
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
						
			elec_area_nm = td_list[area_idx].contents[0]
			if elec_type in [ '10', '11' ]:
				party_nm = ""
				candidate_num = ""
			else:
				party_nm = td_list[party_idx].contents[0].strip()
				if elec_type in [ '8','9']:
					
					candidate_num = td_list[party_idx].contents[2].strip().replace('(','').replace(')','') + "-" + td_list[candnum_idx].contents[0].strip()
				else:
					if len( td_list[candnum_idx].contents ) > 0:
						candidate_num = td_list[candnum_idx].contents[0].strip()
					else:
						candidate_num = ""
				party_nm = td_list[party_idx].contents[0].strip()
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
			#print elec_area_nm, candidate_num, party_nm, name, sex, birthdate #unicode( hanja ), sex, birthdate
			
			candidate_data = [ party_nm, candidate_num, name, hanja, sex, birthdate ]
			candidate_list.append( candidate_data )
			continue
		return_object['elec_nm'] = elec_area_nm.replace( ' ', '' )
	return return_object

import argparse
from argparse import RawTextHelpFormatter

prog_desc = u'2014년 6월 4일 지방선거 후보자 및 선거구 정보 가져오기'
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
elec_type = "3"

max_sgg_num = { '5':{}, '6':{} }
#print elec_type, elec_type_hash[elec_type]

elec_type_list = elec_type_hash.keys()
elec_type_list.sort()

candidate_data_hash = {}
candidate_data_hash[elec_date] = {}
elec_area_hash = {}
elec_area_hash[elec_date] = {}


noresult_keyword = "검색된 결과가 없습니다."


for elec_type in elec_type_list:
	elec_area_hash[elec_date][elec_type] = []
	candidate_data_hash[elec_date][elec_type] = {}
	print "\n", work_type, elec_type, elec_type_hash[elec_type], "data:"
	if elec_type in [ '3','8','11' ]:
		sig_lvl = 1
	else:
		sig_lvl = 2

	area_list = []
	if elec_type == '10': #교육의원. 제주특별자치도 제주시 1, 2, 3 서귀포시 4, 5 선거구. 
		area = area_info.get_area_by_cd( '39', elec_date )
		area_list = [ suba for suba in area.children ]
	else:
		if elec_type in [ '5', '6' ]:
			area_select = area_info.select().where( ( area_info.sig_lvl == sig_lvl ) & ( area_info.valid_from < elec_date ) & ( area_info.valid_to > elec_date ) & ( area_info.nec_cd != None ) & ( area_info.spcity_cd != '1' ) )
		else:
			area_select = area_info.select().where( ( area_info.sig_lvl == sig_lvl ) & ( area_info.valid_from < elec_date ) & ( area_info.valid_to > elec_date ) & ( area_info.nec_cd != None ) & ( area_info.spcity_cd != '2' ) )
		area_list = [ area for area in area_select ]
		print "total", len( area_list ), "areas."

	#print "a"

	for area in area_list:
		#if elec_type == '6' and area.nec_cd == '4302':
			#print elec_type, area.sig_cd, area.sig_nm, area.nec_cd
		if elec_type in [ '3', '4', '8', '9', '11' ]:
			elec_cd = elec_type + area.nec_cd + '00'
		elif elec_type in [ '5', '6', '10' ]:
			elec_area_prefix = elec_type + area.nec_cd
		sggcitycode = '-1'
		towncode = '-1'
		sggtowncode = '0'
		citycode = area.nec_cd[0:2] + '00'

		if elec_type in [ '4', '9' ]:
			sggcitycode = elec_type + area.nec_cd + "00"

		max_num = 30
		if elec_type in [ '5', '6', '10' ]:

			if elec_type in ['5','6']:
				towncode = area.nec_cd

			min_num = 1
			if elec_type == '6' and area.nec_cd == '4302': #청주시 흥덕구 기초의회 선거구 코드는 1 이 아니라 4 에서부터 시작함.. 일종의 코드부여 버그 
				min_num = 4
			for i in range(min_num, max_num):
				if elec_type in ['5','6']:
					sggtowncode = elec_area_prefix + '{:02d}'.format( i )
					elec_cd = sggtowncode
				elif elec_type == '10':
					sggcitycode = elec_area_prefix + '{:02d}'.format( i )
					elec_cd = sggcitycode
					
				sys.stdout.write('.')
						
				#print elec_type, citycode, sggcitycode, towncode, sggtowncode
				htmldata = get_htmldata( elec_type, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = noresult_keyword, local_only = local_only)
				if htmldata == "":
					#print "no data for", elec_type, towncode, sggtowncode, i
					#max_sgg_num[elec_type][towncode] = i - 1
					break
				if i == 1:
					max_num = find_max_elec_area_num( elec_type, htmldata )
				
				if work_mode == 'F':
					result_hash = process_candidate_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata )
					candidate_list = result_hash['candidate_list']
					#print len( candidate_list ), len( elec_area_list )
					elec_nm = result_hash['elec_nm']
					#print elec_nm
					if len( candidate_list ) > 0:
						#print elec_cd, elec_nm
						candidate_data_hash[elec_date][elec_type][elec_cd] = candidate_list
						elec_area_hash[elec_date][elec_type].append( { 'elec_cd': elec_cd, 'elec_nm': elec_nm, 'elec_lvl': elec_type } )

				if i == max_num:
					break
					#if len( elec_area_list ) > 0:	
					#	if elec_area_list[-1]['elec_nm'] == elec_nm:
					#		#print elec_nm
					#		break
				
		else:
			sys.stdout.write('.')
			#print elec_type, citycode, sggcitycode, towncode, sggtowncode
			htmldata = get_htmldata( elec_type, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = noresult_keyword, local_only = local_only )
			if htmldata == "":
				#print "no data for", elec_type, towncode, sggtowncode, i
				#max_sgg_num[elec_type][towncode] = i - 1
				continue
			if work_mode == 'F':
				result_hash = process_candidate_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata )
				candidate_list = result_hash['candidate_list']
				elec_nm = area.sig_nm
	
				if len( candidate_list ) > 0:
					#print elec_cd, elec_nm
					candidate_data_hash[elec_date][elec_type][elec_cd] = candidate_list
					elec_area_hash[elec_date][elec_type].append( { 'elec_cd': elec_cd, 'elec_nm': elec_nm, 'elec_lvl': elec_type } )
		#break

		

#for party in party_hash.keys():
#	print "[", party, "]"
#print max_sgg_num
if work_mode == 'F':
	candidate_data_json = json.dumps( candidate_data_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )
	f = codecs.open("candidate_info_2014-06-04.json", encoding='utf-8', mode='w')
	f.write ( candidate_data_json )
	f.close()

	elec_area_json = json.dumps( elec_area_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )
	f = codecs.open("elec_area_2014-06-04.json", encoding='utf-8', mode='w')
	f.write ( elec_area_json )
	f.close()

