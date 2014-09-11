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
url_template = 'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%23${elec_type}&electionCode=${elec_type}&cityCode=${citycode}&sggCityCode=${sggcitycode}&townCode=${towncode}&sggTownCode=0&x=24&y=11'
'''
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%234&electionCode=4&cityCode=4100&sggCityCode=4410500&townCode=-1&sggTownCode=0&x=40&y=8
http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%235&electionCode=5&cityCode=4100&sggCityCode=-1&townCode=4106&sggTownCode=0&x=30&y=12
'''
#'http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020140604&requestURI=%2Felectioninfo%2F0020140604%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%235&electionCode=5&cityCode=4900&sggCityCode=-1&townCode=4901&sggTownCode=5490101&x=31&y=9'
election_type = {
    1: u"대통령선거",
    2: u"국회의원선거",
    3: u"시·도지사선거",
    4: u"구·시·군의 장선거",
    5: u"시·도의회의원선거",
    6: u"구·시·군의회의원선거",
    8: u"광역의원비례대표선거",
    9: u"기초의원비례대표선거",
    10: u"교육의원선거",
    11: u"교육감선거"
}

nec_sido_list = {
"11":	"서울특별시",
"26":	"부산광역시",
"27":	"대구광역시",
"28":	"인천광역시",
"29":	"광주광역시",
"30":	"대전광역시",
"31":	"울산광역시",
"51":	"세종특별자치시",
"41":	"경기도",
"42":	"강원도",
"43":	"충청북도",
"44":	"충청남도",
"45":	"전라북도",
"46":	"전라남도",
"47":	"경상북도",
"48":	"경상남도",
"49":	"제주특별자치도"
}


def get_htmldata( elec_type, citycode, sggcitycode, towncode ):
    filename = "htmldata/nec_cd_" + elec_type + "_" + citycode + "_" + sggcitycode + "_" + towncode + ".html"
    if os.path.isfile( filename ):
        f = open( filename, "r" )
        data = f.read()
        f.close()

    else: #file not exist
        url = Template( url_template). substitute( { 'elec_type': elec_type, 'citycode' : citycode, 'sggcitycode': sggcitycode, 'towncode': towncode} )
        #print url
        data = urllib2.urlopen(url).read()
        f = open( filename, 'w' )
        #f = codecs.open( filename, encoding='utf-8', mode='w')
        f.write ( data )
        f.close()


    return data



log_str = ""
elec_type_list = [ "4", "5" ]
elec_date = "2014-06-04"

area_info_nec_cd = {}
area_info_nec_cd[elec_date] = {}


for elec_type in elec_type_list:
    print elec_date, elec_type
    for sido_cd in nec_sido_list.keys():
        sido = area_info.get( ( area_info.sig_nm == nec_sido_list[sido_cd] ) & ( area_info.valid_from < elec_date ) & ( area_info.valid_to > elec_date ) )

        area_info_nec_cd[elec_date][sido.sig_cd] = { 'sig_cd': sido.sig_cd, 'sig_nm': sido.sig_nm, 'nec_cd': sido_cd }

        #print sido.sig_nm, sido.sig_cd, sido_cd
        #citycode, sggcitycode, towncode
        if elec_type == '4':
            citycode = sido_cd + "00"
            sggcitycode = elec_type + sido_cd + "0100"
            towncode = '-1'
        elif elec_type == '5':
            citycode = sido_cd + "00"
            sggcitycode = "-1"
            if sido_cd == '51': #세종시
                towncode = sido_cd + "01"
            else:
                towncode = sido_cd + "05"
        sido.nec_cd = sido_cd
        #sido.save()
        #sgg_cd = elec_type + sido_cd[:3] + "100"

        data = get_htmldata( elec_type, citycode, sggcitycode, towncode )
        html = BeautifulSoup( data )

        if elec_type == '4':
            select_control = html.find( id='sggCityCode' )
        elif elec_type == '5':
            select_control = html.find( id='townCode' )

        option_list = select_control.find_all( 'option' )
        for o in option_list[1:]:
            #print o['value'], o.contents[0]
            if elec_type == '4':
                nec_cd = o['value'][1:5]
            elif elec_type == '5':
                nec_cd = o['value']
            area_nm = o.contents[0]
            #print nec_cd, area_nm
            try:
                area = area_info.search_by_name( unicode( area_nm ), elec_date, sig_lvl = '2', parent_id = sido.id )
            except area_info.DoesNotExist:
                print "no such area", area_nm, nec_cd
                continue
            area_info_nec_cd[elec_date][area.sig_cd] = { 'sig_cd': area.sig_cd, 'sig_nm': area.sig_nm, 'nec_cd': nec_cd }
            #print area.sig_cd, area.sig_nm, nec_cd
            #area.nec_cd = nec_cd
            #area.save()

nec_cd_json = json.dumps( area_info_nec_cd, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )

f = codecs.open("area_info_nec_cd.json", encoding='utf-8', mode='w')
f.write ( nec_cd_json )
f.close()

