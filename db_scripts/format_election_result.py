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


import urllib2
from bs4 import BeautifulSoup

from string import Template

url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020120411&requestURI=%2Felectioninfo%2F0020120411%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%232&electionCode=2&cityCode=${citycode}&sggCityCode=0&x=36&y=1'
#'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020120411&requestURI=%2Felectioninfo%2F0020120411%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%232&electionCode=2&cityCode=${citycode}&sggCityCode=${elec_area_cd}&proportionalRepresentationCode=-1&townCode=-1&sggTownCode=-1&dateCode=0&x=28&y=6'

def get_data( citycode ):
    filename = "result_html/" + citycode + "_result.html"
    if os.path.isfile( filename ):
        f = open( filename, "r" )
        data = f.read()
        f.close()

    else: #file not exist
        url = Template( url_template). substitute( { 'citycode': citycode } )

        data = urllib2.urlopen(url).read()
        f = open( filename, 'w' )
        #f = codecs.open( filename, encoding='utf-8', mode='w')
        f.write ( data )
        f.close()


    return data

elec_area_data = []
if os.path.isfile( data_filename  ):
    f = open( data_filename, 'r')
    elec_area_data = yaml.load(f)
    f.close()
del elec_area_data[1]

log_str = ""

''' 2012-04-11 총선 결과'''
elec_date = '2012-04-11'

try:
    election = election_info.get( election_info.elec_date == elec_date )
except election_info.DoesNotExist:
    print "no such election"
elec_type = '2'
election_result = {}
election_result[elec_date] = {}
election_result[elec_date][elec_type] = {}

#filename = 'election_result_2012-04-11.json'
##print filename
#json_file = open( filename, 'r' )
#json_data = json_file.read()
#json_file.close()
#election_result = json.loads( json_data )


for k in elec_area_data.keys():
    citycode = k
    print citycode

    data = get_data( str( citycode ) )
    html = BeautifulSoup( data )
    elec_cd_prefix = '2' + str( citycode )[:2] + '%'

    table = html.find( id='table01' )
    tbody = table.tbody
    sum_mode = False
    single_area = False
    multi_area = False
    for tr in tbody.find_all( 'tr' ):
        td_list = tr.find_all( 'td' )

        if len( td_list[0].contents ) > 0: #후보자 목록
            candidate_list = []
            elec_area_nm = td_list[0].contents[0]

            try:
                ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_area_nm.encode( 'utf-8' ) ) & ( elec_area_info.elec_cd % elec_cd_prefix ) )
            except elec_area_info.DoesNotExist:
                print "no such elec_area", elec_area_nm
            election_result[elec_date][elec_type][ea.elec_cd] = { 'elec_cd': ea.elec_cd, 'elec_nm': ea.elec_nm, 'vote_result': [], 'candidate_result': []}
            print ea.elec_cd, ea.elec_nm
            candidate_list = td_list[4:]
            for candidate in td_list:
                st = candidate.find( 'strong' )

                if st != None and len( st.contents ) == 3:
                    party_nm = st.contents[0]
                    person_nm = st.contents[2]
                    try:
                        party = party_info.get( ( party_info.party_nm == party_nm.encode( 'utf-8' ) ) & ( party_info.valid_from < elec_date ) & ( party_info.valid_to > elec_date) )
                    except party_info.DoesNotExist:
                        print "no such party", party_nm

                    try:
                        candidate = candidate_info.get( ( candidate_info.election_info == election.id ) & ( candidate_info.elec_area_info == ea.id ) & ( candidate_info.party_info == party.id ) )
                    except candidate_info.DoesNotExist:
                        print "no such candidate", election.elec_title, ea.elec_nm, party.party_nm, person_nm

                    #print party_nm, person_nm
                    election_result[elec_date][elec_type][ea.elec_cd]['candidate_result'].append(
                        { 'candidate_num': candidate.candidate_num, 'party_nm': party_nm, 'person_nm': person_nm, 'sex': candidate.person_info.sex } )
            sum_mode = False
            single_area = False
            multi_area = False
        else: # 선거결과
            if td_list[1].contents[0] == u"소계": # 소계 라인
                sum_mode = True
            else: #시군구 라인
                if sum_mode == False: # 단일행정구역
                    single_area = True
                else: # 복수 행정구역
                    multi_area = True
            if ( sum_mode == True and multi_area == False ) or single_area == True:
                total_num = int( td_list[2].contents[0].replace( ',', '' ) )
                vote_sum = int( td_list[3].contents[0].replace( ',', '' ) )
                #vote_sum = int( td_list[3].contents[0] )
                num_candidate = len( election_result[elec_date][elec_type][ea.elec_cd]['candidate_result'] )
                for i in xrange( num_candidate ):
                    vote_count = int( td_list[4+i].contents[0].replace( ',', '' ) )
                    vote_percent = float( td_list[4+i].contents[2].replace( ',', '' ).replace('(','').replace(')','') )
                    election_result[elec_date][elec_type][ea.elec_cd]['candidate_result'][i]['vote_count'] = vote_count
                    election_result[elec_date][elec_type][ea.elec_cd]['candidate_result'][i]['vote_percent'] = vote_percent
                    #vote_sum = int( td_list[3].contents[0] )
                invalid_count = int( td_list[15].contents[0].replace( ',', '' ) )
                abstention_count = int( td_list[16].contents[0].replace( ',', '' ) )
                election_result[elec_date][elec_type][ea.elec_cd]['vote_result'] = \
                    { 'eligible_count': total_num, 'vote_count': vote_sum, 'invalid_count':invalid_count, 'abstention_count':abstention_count }


election_result_json = json.dumps( election_result, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )

f = codecs.open("election_result_2012-04-11.json.", encoding='utf-8', mode='w')
f.write ( election_result_json )
f.close()

#f = codecs.open("candidate.log.", encoding='utf-8', mode='w')
#f.write ( log_str )
#f.close()


#print elec_area_data