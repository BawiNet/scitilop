#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import time
import codecs
import os.path
from election_class import *
import urllib2
from bs4 import BeautifulSoup

from string import Template

#url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%23${electioncode}&electionCode=${electioncode}&cityCode=${citycode}&sggCityCode=${sggcitycode}&townCode=${towncode}&sggTownCode=${sggtowncode}&x=38&y=15'

url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%23${electioncode}&electionCode=${electioncode}&cityCode=${citycode}&sggCityCode=${sggcitycode}&townCode=${towncode}&sggTownCode=${sggtowncode}&x=31&y=12'
''' 선거결과 URL 형식
'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%234&electionCode=4&cityCode=1100&sggCityCode=4110100&townCode=-1&sggTownCode=0&x=39&y=11'
'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%235&electionCode=5&cityCode=1100&sggCityCode=0&townCode=1101&sggTownCode=0&x=38&y=9'
'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%236&electionCode=6&cityCode=1100&sggCityCode=0&townCode=1101&sggTownCode=0&x=29&y=9'
'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%238&electionCode=8&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=32&y=10'
'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%239&electionCode=9&cityCode=1100&sggCityCode=9110100&townCode=-1&sggTownCode=0&x=23&y=9'
'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%2310&electionCode=10&cityCode=4900&sggCityCode=0&townCode=-1&sggTownCode=0&x=47&y=9'
'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%2311&electionCode=11&cityCode=1100&sggCityCode=0&townCode=-1&sggTownCode=0&x=31&y=8'
'''

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

	filename = "htmldata/result_2014-06-04_" + electioncode + "_" + citycode + "_" + sggcitycode + "_" + towncode + "_" + sggtowncode + ".html"
	#print filename
	if os.path.isfile( filename ):
		#print "yes file"
		f = open( filename, "r" )
		data = f.read()
		f.close()

	else: #file not exist
		#print "no file"
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

def process_result_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata ):

	#candidate_list = []
	result_hash = {}
	election = election_info.get( election_info.elec_date == elec_date )

	html = BeautifulSoup( htmldata )
	table = html.find( id='table01' )
	if table == None:
		return result_hash
	else:
		tbody = table.tbody
		ea = None
		elec_cd = ""
		if elec_type in ['3', '8', '11' ]:
			elec_cd = elec_type + citycode
		elif elec_type in [ '4', '9']:
			elec_cd = sggcitycode
		if elec_cd != "":
			try:
				ea = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
			except elec_area_info.DoesNotExist:
				print "no such elec_area"

		for tr in tbody.find_all( 'tr' ):
			party_list = []
			candidate_list = []
			result_list = []
			td_list = tr.find_all( 'td' )
			elec_nm = ""
			elec_cd = ""

			if elec_type in ['3', '11' ]:
				print td_list[0]
				if len( td_list[0].contents ) == 0:
					candidate_list = td_list[3:]
				else:
					td0 = td_list[0].contents[0].strip()
					print td0.encode( 'utf-8')
					if td0 == u'합계':
						result_list = td_list[1:]
			elif elec_type in ['4']:
				if len( td_list[1].contents ) == 0:
					candidate_list = td_list[4:]
					#elec_nm = td_list[0].contents[0]
				elif len( td_list[0].contents ) == 0:
					result_list = td_list[2:]
			elif elec_type in ['5','6','10']:
				if len( td_list[0].contents ) > 0:
					candidate_list = td_list[4:]
					ea = None
					elec_nm = td_list[1].contents[0]
				else:
					result_list = td_list[2:]
			elif elec_type in ['8']:
				if len( td_list[0].contents ) == 0:
					party_list = td_list[3:]
				else:
					td0 = td_list[0].contents[0].strip()
					print td0.encode( 'utf-8')
					if td0 == u'합계':
						result_list = td_list[1:]
			elif elec_type in ['9']:
				if len( td_list[0].contents ) == 0:
					party_list = td_list[3:]
				else:
					result_list = td_list[1:]

			if ea == None:

				if elec_nm != "":
					#print ord( elec_nm[7] ), elec_nm[7]
					elec_nm = elec_nm.replace( u' ','')
					#print elec_nm
					elec_cd_prefix = elec_type + citycode[:2] + '%'
					print elec_cd_prefix
					try:
						ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_nm.encode( 'utf-8') ) & ( elec_area_info.elec_lvl == elec_type ) & ( elec_area_info.elec_cd % elec_cd_prefix )  )
					except elec_area_info.DoesNotExist:
						print "no such elec area", elec_nm
					print ea.elec_cd, ea.elec_nm
				elif elec_cd != "":
					try:
						ea = elec_area_info.get( ( elec_area_info.elec_cd == elec_cd ) & ( elec_area_info.elec_lvl == elec_type ) )
					except elec_area_info.DoesNotExist:
						print "no such elec area", elec_cd

			if not ea.elec_cd in result_hash.keys():
				result_hash[ea.elec_cd] = { 'candidate_result': [], 'vote_result': {} }

			print ea.elec_cd, ea.elec_nm
			for cand in candidate_list:
				#print cand
				st = cand.find( 'strong' )
				if st == None:
					break
				if len( st.contents ) == 3:
					party_nm = st.contents[0]
					person_nm = st.contents[2]
				elif len( st.contents ) == 1 and elec_type == '11':
					person_nm = st.contents[0]
				else:
					continue

				if elec_type in [ '10', '11' ]:
					party_id = None
					party_nm = ""
				else:
					try:
						party = party_info.get( ( party_info.party_nm == party_nm.encode( 'utf-8' ) ) & ( party_info.valid_from < elec_date ) & ( party_info.valid_to > elec_date) )
					except party_info.DoesNotExist:
						print "no such party", party_nm
					party_id = party.id

				try:
					candidate_select = candidate_info.select().join( person_info ).where( ( candidate_info.party_info == party_id ) &
																													( person_info.name == person_nm.encode( 'utf-8' ) ) &
																													( candidate_info.elec_area_info == ea.id ) &
																													( candidate_info.election_info == election.id ) )
				except candidate_info.DoesNotExist:
					print "no such candidate", election.elec_title, ea.elec_nm, party.party_nm, person_nm
				c_list = [ c for c in candidate_select ]
				if len( c_list ) == 1:
					candidate = c_list[0]
				else:
					print election.elec_title, ea.elec_nm, party_nm, person_nm, "candidate_select", len( c_list), c_list
				c_hash = { 'candidate_num': candidate.candidate_num, 'party_nm': party_nm, 'person_nm': person_nm, 'sex': candidate.person_info.sex }
				#result_hash[ea.elec_cd]['candidate_result'].append( [ candidate.candidate_num, party_nm, person_nm, candidate.person_info.sex ] )
				result_hash[ea.elec_cd]['candidate_result'].append( c_hash )

			for part in party_list:
				st = part.find( 'strong' )
				if st != None and len( st.contents ) > 0:
					party_nm = st.contents[0]
					if party_nm not in [ p['party_nm'] for p in result_hash[ea.elec_cd]['candidate_result'] ]:
						try:
							party = party_info.get( ( party_info.party_nm == party_nm.encode( 'utf-8' ) ) & ( party_info.valid_from <= elec_date ) & ( party_info.valid_to >= elec_date) )
						except party_info.DoesNotExist:
							print "no such party", party_nm
						party_hash = { 'candidate_num': "", 'party_nm': party_nm, 'person_nm': "", 'sex': ""}
						#result_hash[ea.elec_cd]['candidate_result'].append( [ "", party_nm, "", "" ] )
						result_hash[ea.elec_cd]['candidate_result'].append( party_hash )
			#print result_hash[ea.elec_cd]['candidate_result']
			#print result_list
			if len( result_list ) > 0:
				#print result_list[0]
				#print result_list[1]
				#print result_list[2]
				total_num = int( result_list[0].contents[0].replace( ',', '' ) )
				vote_sum = int( result_list[1].contents[0].replace( ',', '' ) )
				num_candidate = len( result_hash[ea.elec_cd]['candidate_result'] )
				for i in xrange( num_candidate ):
					#print i, num_candidate
					vote_count = int( result_list[2+i].contents[0].replace( ',', '' ) )
					vote_percent = float( result_list[2+i].contents[2].replace( ',', '' ).replace('(','').replace(')','') )
					if 'vote_count' in result_hash[ea.elec_cd]['candidate_result'][i].keys():
						result_hash[ea.elec_cd]['candidate_result'][i]['vote_count'] += vote_count
						result_hash[ea.elec_cd]['candidate_result'][i]['vote_percent'] = 0
					else:
						result_hash[ea.elec_cd]['candidate_result'][i]['vote_count'] = vote_count
						result_hash[ea.elec_cd]['candidate_result'][i]['vote_percent'] = vote_percent
					#vote_sum = int( td_list[3].contents[0] )
				invalid_count = int( result_list[-3].contents[0].replace( ',', '' ) )
				abstention_count = int( result_list[-2].contents[0].replace( ',', '' ) )
				result_hash[ea.elec_cd]['vote_result']['eligible_count'] = total_num
				result_hash[ea.elec_cd]['vote_result']['vote_count'] = vote_sum
				result_hash[ea.elec_cd]['vote_result']['invalid_count'] = invalid_count
				result_hash[ea.elec_cd]['vote_result']['abstention_count'] = abstention_count

		#return_object['elec_nm'] = elec_area_nm.replace( ' ', '' )
	for elec_cd in result_hash.keys():
		for c in result_hash[elec_cd]['candidate_result']:
			#print c
			if c['vote_percent'] == 0:
				c['vote_percent'] = ( round( ( float( c['vote_count'] ) / float( result_hash[elec_cd]['vote_result']['vote_count'] - result_hash[elec_cd]['vote_result']['invalid_count'] ) ) * 10000 ) ) / 100
	return result_hash

import argparse
from argparse import RawTextHelpFormatter

prog_desc = u'2014년 6월 4일 지방선거 선거결과 가져오기'
parser = argparse.ArgumentParser(description=prog_desc, formatter_class=RawTextHelpFormatter)

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

election_result_hash = {}
election_result_hash[elec_date] = {}

noresult_keyword = "검색된 결과가 없습니다."

for elec_type in elec_type_list:
	election_result_hash[elec_date][elec_type] = {}
	print "\n", work_type, elec_type, elec_type_hash[elec_type], "data:"
	if elec_type in [ '3','8','11' ]:
		sig_lvl = 1
	else:
		sig_lvl = 2

	area_list = []

	if elec_type == '10': #교육의원. 제주특별자치도 제주시 1, 2, 3 서귀포시 4, 5 선거구.
		area = area_info.get_area_by_cd( '39', elec_date )
		area_list.append( area )
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

		if elec_type in ['5','6']:
			towncode = area.nec_cd

		sys.stdout.write('.')
		htmldata = get_htmldata( elec_type, citycode, sggcitycode, towncode, sggtowncode, noresult_keyword = noresult_keyword, local_only = local_only )
		print elec_type, citycode, sggcitycode, towncode, sggtowncode, type(htmldata)
		if htmldata == "":
			#print "no data for", elec_type, towncode, sggtowncode, i
			#max_sgg_num[elec_type][towncode] = i - 1
			continue

		if work_mode == 'F':
			result_hash = process_result_html( elec_type, elec_date, citycode, sggcitycode, towncode, sggtowncode, htmldata )
			for key in result_hash:
				election_result_hash[elec_date][elec_type][key] = result_hash[key]

#for party in party_hash.keys():
#	print "[", party, "]"
#print max_sgg_num
if work_mode == 'F':
	election_result_json = json.dumps( election_result_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )
	f = codecs.open("election_result_" + elec_date + ".json", encoding='utf-8', mode='w')
	f.write ( election_result_json )
	f.close()

