#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, traceback 
import json
import os
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs
from election1406 import *

#
# MAIN
#

#sys.exit(0)

election_type_reverse = {
    u"교육감" : 1,
    u"시도지사" : 2,
    u"광역비례" : 3,
    u"광역의회의원" : 4,
    u"기초단체장" : 5,
    u"기초의회의원" : 6,
    u"기초비례" : 7,
    u"교육의원" : 8
}

election_type = {
    1: u"교육감",
    2: u"시도지사",
    3: u"광역비례",
    4: u"광역의회의원",
    5: u"기초단체장",
    6: u"기초의회의원",
    7: u"기초비례",
    8: u"교육의원",
}

def get_emd_cd_from_sgg_cd(sgg_cd):
    """시군구 코드 하위 모든 읍면동 코드를 다 들고 온다."""
    qry = Area_Info.select(Area_Info.sig_cd).where(fn.Substr(Area_Info.sig_cd, 1, 5) == sgg_cd, Area_Info.sig_lvl == 3)

    return [x.sig_cd for x in qry]

def get_area_full_info_from_emd(emd_cd):
    """읍면동 코드에 대응하는 광역-시군구-읍면동 이름을 리스트형식으로 제시한다"""

    if (len(emd_cd) == 7):
        qry_emd = Area_Info.select(Area_Info.sig_nm).where(Area_Info.sig_cd == emd_cd)
        emd = qry_emd[0].sig_nm
    elif (len(emd_cd) == 5):
        emd = u"N/A" 
        emd_cd = emd_cd + u"00"
    else:
        print "ERROR: Not appropriate number"
        return None

    qry_sgg = Area_Info.select(Area_Info.sig_nm).where(Area_Info.sig_cd == emd_cd[:5])
    qry_prv = Area_Info.select(Area_Info.sig_nm).where(Area_Info.sig_cd == emd_cd[:2])

    prv = qry_prv[0].sig_nm
    sgg = qry_sgg[0].sig_nm

    return [prv, sgg, emd]

def get_candidates_from_emd(emd_cd):
    """모든 읍면동자료에서 모든 선거결과와 후보목록을 SQL로 뽑아낼 수 있다.
       다만 주의할 것은, 분동된 경우 두 번 나올 수 있다는 점. 그리고 이 때
       후보가 다를 수 있다는 점이다."""

    # it is important to keep the joining order area_info -> election_info -> candidate_info
    qry = Area_Info.select(
                            Election_Info.elec_type, 
                            Election_Info.precinct,
                            Candidate_Info.name,
                            Candidate_Info.party,
                            Election_Info.count_type,
                            Election_Info.count,
                        ).join(Election_Info).join(Candidate_Info).where(
                            Election_Info.sig_cd == emd_cd,
                            Election_Info.count_type == u'일반'
                        ).order_by(
                            Election_Info.elec_type,
                            Candidate_Info.id
                        ).naive()

    columns = []
    for e in qry:
        column_str = e.elec_type + "_" + e.precinct + "_" + e.name + "(" + e.party + ")"
        columns.append(column_str.encode('utf8'))

    return columns


#
# 730 BIELECTION
#

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

for area in area_data.keys():
    print election_area_data[area]
    print "=========================="
    for cd in area_data[area]:
        if len(cd) == 5:
            emd_cds = get_emd_cd_from_sgg_cd(cd)
        elif len(cd) == 7:
            emd_cds = [cd]
        else:
            print "ERROR: no code match : %s" % cd
            sys.exit(0)

        for emd_cd in emd_cds:
            emd_info = [x.encode('utf8') for x in get_area_full_info_from_emd(emd_cd)]
            candidate_info = get_candidates_from_emd(emd_cd)
            print "\t".join([emd_cd.encode('utf8'),] + emd_info + candidate_info)
            raw_input()


