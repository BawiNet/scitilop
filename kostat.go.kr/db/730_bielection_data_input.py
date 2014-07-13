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
election_area_data = { "11202":"서울시 동작구 을",
									"3005": "대전시 대덕구",
									"31022": "울산시 남구 을",
									"29052": "광주시 광산구 을",
									"2691": "부산시 해운대구 기장군 갑",
									"41152": "경기도 평택시 을",
									"4102": "경기도 수원시 권선구",
									"4103": "경기도 수원시 팔달구",
									"4104": "경기도 수원시 영통구",
									"4139": "경기도 김포시",
									"4303": "충청북도 충주시",
									"3691": "전라남도 담양군 함평군 영광군 장성군",
									"3692": "전라남도 나주시 화순군",
									"3693": "전라남도 순천시 곡성군",
									"4491": "충청남도 서산시 태안군"
								}


area_data = {"11202":["1120053","1120071","1120063","1120073","1120065","1120066","1120067"], 
					 	"3005":["25050"], 
					 	"31022":["2602056","2602057","2602061","2602062","2602063","2602064"], 
					 	"29052":["2405061","2405069","2405070","2405073","2405074","2405075","2405063","2405064"], 
						"2691":["2109053","2109051","2109052","2109070","2109058","2109059","2109071","2109061","2109062","2109063","2109064","2109065","21310"], 
						"41152":["3107011","3107012","3107013","3107033","3107034","3107035","3107037","3107059","3107060","3107062","3107063"], 
						"4102":["31012"], 
						"4103":["31013"], 
						"4104":["31014"], 
						"4139":["31230"], 
						"4303":["33020"], 
						"3691":["36310","36430","36440","36450"], 
						"3692":["36040","36370"], 
						"3693":["36030","36320"], 
						"4491":["34050","34380"] 
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
	elec_area.valid_from = date( "2014-04-01" )
	elec_area.valid_to = date( "9999-12-31" )
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