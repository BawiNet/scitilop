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
from xlwt import Workbook

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

def get_standard_info_from_emd(emd_cd, et):
    """읍면동 결과에서, 각 선거결과별 투표수 총합(분동 고려), 득표율 계산"""
    """et means the code to look up for election_type"""

    # test case
    # 2308068 : 검단1동 (검단5동 결과랑 두 가지가 다 있음)

    # 유효투표수
    vote_sum = Area_Info.select().join(Election_Info).join(Candidate_Info).where(
                            Election_Info.sig_cd == emd_cd,
                            Election_Info.count_type == u'일반',
                            Election_Info.elec_type == election_type[et]
                        ).aggregate(fn.Sum(Election_Info.count).alias('sum'))

    # 각 후보별 투표수
    qry = Area_Info.select(
                            Election_Info.elec_type, 
                            Election_Info.precinct,
                            Candidate_Info.name,
                            Candidate_Info.party,
                            Election_Info.count_type,
                            Election_Info.count,
                            fn.Sum(Election_Info.count).alias('vsum'),
                        ).join(Election_Info).join(Candidate_Info).where(
                            Election_Info.sig_cd == emd_cd,
                            Election_Info.count_type == u'일반',
                            Election_Info.elec_type == election_type[et]
                        ).group_by(
                            Election_Info.candidate_id
                        #).order_by(
                        #    Election_Info.elec_type,
                        #    Candidate_Info.id
                        ).naive()

    header = {}
    votes  = {}
    rvotes = {}
    for e in qry:
        header[e.name] = election_type[et] + "_" + e.party
        #header[e.name] = e.party.encode('utf8')
        votes[e.name]  = str(e.vsum)
        rvotes[e.name] = "%.4f" % (float(e.vsum) / float(vote_sum))


    return { 'header' : header,
             'vote' : votes,
             'ratio' : rvotes } 


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
                            Election_Info.count_type == u'일반',
                            (Election_Info.elec_type == election_type[2])|
                            (Election_Info.elec_type == election_type[3])|
                            (Election_Info.elec_type == election_type[4])|
                            (Election_Info.elec_type == election_type[7])
                        ).order_by(
                            Election_Info.elec_type,
                            Candidate_Info.id
                        ).naive()

    columns = []
    for e in qry:
        column_str = e.elec_type + "_" + e.precinct + "_" + e.name + "(" + e.party + ")"
        columns.append(column_str.encode('utf8'))

    return columns


def is_list_same(list1, list2):
    if len(list1) != len(list2):
        return False

    for i in range(len(list1)):
        if list1[i] != list2[i]:
            return False

    return True

#
# 730 BIELECTION
#

election_info_data = { 'elec_title': "2014년 7.30 재보궐선거", 
							 'elec_lvl':"4", 
							 'elec_date':"2014-07-30" }
election_area_data = { "2112002":u"서울특별시 동작구을",
									"2300501": u"대전광역시 대덕구",
									"2310202": u"울산광역시 남구을",
									"2290502": u"광주광역시 광산구을",
									"2260901": u"부산광역시 해운대구기장군갑",
									"2411502": u"경기도 평택시을",
									"2410201": u"경기도 수원시을",
									"2410301": u"경기도 수원시병",
									"2410401": u"경기도 수원시정",
									"2413901": u"경기도 김포시",
									"2430301": u"충청북도 충주시",
									"2462202": u"전라남도 담양군함평군영광군장성군",
									"2460601": u"전라남도 나주시화순군",
									"2460402": u"전라남도 순천시곡성군",
									"2440501": u"충청남도 서산시태안군"
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

book = Workbook()

for area in area_data.keys():
    print election_area_data[area]
    print "=========================="
    sheet = book.add_sheet(election_area_data[area])
    old_header = None
    row_count = 0
    for cd in area_data[area]:
        if len(cd) == 5:
            emd_cds = get_emd_cd_from_sgg_cd(cd)
        elif len(cd) == 7:
            emd_cds = [cd]
        else:
            print "ERROR: no code match : %s" % cd
            sys.exit(0)

        row = []
        for emd_cd in emd_cds:
            # print header
            emd_info = get_area_full_info_from_emd(emd_cd)
            vote_info1 = get_standard_info_from_emd(emd_cd, election_type_reverse[u'시도지사']);
            vote_info2 = get_standard_info_from_emd(emd_cd, election_type_reverse[u'광역비례']);
            vote_info3 = get_standard_info_from_emd(emd_cd, election_type_reverse[u'기초단체장']);
            vote_info4 = get_standard_info_from_emd(emd_cd, election_type_reverse[u'기초비례']);


            header = "\t".join([emd_cd,] + emd_info + 
                                vote_info1['header'].values() + vote_info1['header'].values() +
                                vote_info2['header'].values() + vote_info2['header'].values() +
                                vote_info3['header'].values() + vote_info3['header'].values() +
                                vote_info4['header'].values() + vote_info3['header'].values() 
                            )
            row = "\t".join([emd_cd,] + emd_info + 
                                vote_info1['vote'].values() + vote_info1['ratio'].values() +
                                vote_info2['vote'].values() + vote_info2['ratio'].values() +
                                vote_info3['vote'].values() + vote_info3['ratio'].values() +
                                vote_info4['vote'].values() + vote_info4['ratio'].values() 
                            )

            if old_header is None or not is_list_same(old_header.split('\t')[4:], header.split('\t')[4:]):
                old_header = header

                header_cells = header.split('\t')
                for i in range(len(header_cells)):
                    sheet.write(row_count, i, header_cells[i])
                row_count = row_count + 1

            row_cells = row.split('\t')
            for i in range(len(row_cells)):
                sheet.write(row_count, i, row_cells[i])
            row_count = row_count + 1
        sheet.flush_row_data()
        book.save('20140730_bielection.xls')

