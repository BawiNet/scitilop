#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import mysql.connector
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs

from election_class import *

election_info_data = { 'elec_title': "2014년 7.30 재보궐선거", 
							 'elec_lvl':"4", 
							 'elec_date':"2014-07-30" }
election_area_data = { "2112002":"서울특별시 동작구을",
									"2300501": "대전광역시 대덕구",
									"2310202": "울산광역시 남구을",
									"2290502": "광주광역시 광산구을",
									"2260901": "부산광역시 해운대구기장군갑",
									"2411502": "경기도 평택시을",
									"2410201": "경기도 수원시을",
									"2410301": "경기도 수원시병",
									"2410401": "경기도 수원시정",
									"2413901": "경기도 김포시",
									"2430301": "충청북도 충주시",
									"2462202": "전라남도 담양군함평군영광군장성군",
									"2460601": "전라남도 나주시화순군",
									"2460402": "전라남도 순천시곡성군",
									"2440501": "충청남도 서산시태안군"
								}


area_data = {"2112002":["1120053","1120071","1120063","1120073","1120065","1120066","1120067"], 
						"2300501":["25050"], 
						"2310202":["2602056","2602057","2602061","2602062","2602063","2602064"], 
						"2290502":["2405061","2405069","2405070","2405073","2405074","2405075","2405063","2405064"], 
						"2260901":["2109053","2109051","2109052","2109070","2109058","2109059","2109071","2109061","2109062","2109063","2109064","2109065","21310"], 
						"2411502":["3107011","3107012","3107013","3107033","3107034","3107035","3107037","3107059","3107060","3107062","3107063"], 
						"2410201":["31012"], 
						"2410301":["31013"], 
						"2410401":["31014"], 
						"2413901":["31230"], 
						"2430301":["33020"], 
						"2462202":["36310","36430","36440","36450"], 
						"2460601":["36040","36370"], 
						"2460402":["36030","36320"], 
						"2440501":["34050","34380"] 
					}

election_data = { "2014-07-30": area_data.keys() }

elec = election_info()
elec.elec_date = election_info_data['elec_date']
elec.elec_lvl = election_info_data['elec_lvl']
elec.elec_title = election_info_data['elec_title']
elec.save()

for elec_cd in election_area_data.keys():
	elec_area = elec_area_info()
	elec_area.elec_cd = elec_cd 
	elec_area.elec_nm = election_area_data[elec_cd]
	elec_area.elec_lvl = "2"
	elec_area.valid_from = "2014-04-01" 
	elec_area.valid_to = "9999-12-31" 
	elec_area.save()
							
for elec_cd in area_data.keys():
	for elec_area in elec_area_info.select().where( elec_area_info.elec_cd == elec_cd ):
		print elec_cd, elec_area.elec_nm
		for sig_cd in area_data[elec_cd]:
			for area in area_info.select().where( area_info.sig_cd == sig_cd ):
				print "  ",area.sig_cd, area.sig_nm
				ea_rel = elec_area_relation()
				ea_rel.elec_area_info = elec_area.id
				ea_rel.area_info = area.id
				ea_rel.save()

for elec_date in election_data.keys():
	for elec in election_info.select().where( election_info.elec_date == elec_date ):
		election_id = elec.id
		print elec.elec_title, elec.elec_date, elec.elec_lvl
		for elec_area in elec_area_info.select().where( elec_area_info.elec_cd << election_data[str(elec.elec_date)] ):
			print elec_area.elec_cd, elec_area.elec_nm
			elec_area_id = elec_area.id
			eea_rel = elec_elec_area_relation()
			eea_rel.election_info = election_id
			eea_rel.elec_area_info = elec_area_id
			eea_rel.save()