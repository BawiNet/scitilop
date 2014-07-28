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

import yaml
import os.path
data_filename = "./elec_area_code_20120411.txt"


import urllib2
from bs4 import BeautifulSoup

from string import Template
url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020120411&requestURI=%2Felectioninfo%2F0020120411%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%232&electionCode=2&cityCode=${citycode}&sggCityCode=${elec_area_cd}&proportionalRepresentationCode=-1&townCode=-1&sggTownCode=-1&dateCode=0&x=28&y=6'

def get_data( citycode, elec_area_cd ):
	filename = "candidate_html/" + citycode + "_" + elec_area_cd + ".html"
	if os.path.isfile( filename ):
		f = open( filename, "r" )
		data = f.read()
		f.close()

	else: #file not exist
		url = Template( url_template). substitute( { 'citycode': citycode, 'elec_area_cd' : elec_area_cd } )
			
		data = urllib2.urlopen(url).read()
		f = open( filename, 'w' )
		#f = codecs.open( filename, encoding='utf-8', mode='w')
		f.write ( data )
		f.close()
		
		
	return data


if os.path.isfile( data_filename  ):
	f = open( data_filename, 'r')
	elec_area_data = yaml.load(f)
	f.close()

filename = 'candidate_info.json'
json_file = open( filename, 'r' )
candidate_data_hash = json.load( json_file )
json_file.close()

log_str = ""

''' 2012-04-11 총선 후보자 목록 '''
elec_date = '2012-04-11'
candidate_data_hash[elec_date] = {}


for k in elec_area_data.keys():
	citycode = k 
	elec_area_hash = elec_area_data[citycode]
	for elec_area_cd in elec_area_hash.keys():
		#elec_area_cd = elec_area.keys()[0]
		elec_area_nm = elec_area_hash[elec_area_cd]
		print citycode, elec_area_cd, elec_area_nm
		#continue
		candidate_data_hash[elec_date][elec_area_cd] = []
		data = get_data( str( citycode ) , str( elec_area_cd ) )
		html = BeautifulSoup( data )

		table = html.find( id='table01' )
		tbody = table.tbody
		for tr in tbody.find_all( 'tr' ):
			td_list = tr.find_all( 'td' )
			area_nm = td_list[0].contents[0]
			candidate_num = int( td_list[2].contents[0].strip() )
			party_nm = td_list[3].contents[0].strip()
			name_array = td_list[4].contents
			name = name_array[0].strip()
			hanja = name_array[2][1:-1]
			sex = td_list[5].contents[0]
			if sex == u'남':
				sex = 'M'
			else:
				sex = 'F'
			y, m, d = td_list[6].contents[0].split( '/' )
			birthdate= str( date( int( y ), int( m ), int( d ) ) )
			
			
			candidate_data_hash[elec_date][elec_area_cd].append( [ party_nm, candidate_num, name, hanja, sex, birthdate ] )
			log_str += str( elec_area_cd ) + "\t" + str( candidate_num ) + "\t" + party_nm + "\t"  + name + "\t" + hanja + "\t" + sex + "\t" + birthdate + "\n"


candidate_data_json = json.dumps( candidate_data_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )

f = codecs.open("candidate_info.json", encoding='utf-8', mode='w')
#f = open("candidate_info_new.json.", mode='w')
f.write ( candidate_data_json )
f.close()

#f = codecs.open("candidate.log.", encoding='utf-8', mode='w')
#f.write ( log_str )
#f.close()


#print elec_area_data