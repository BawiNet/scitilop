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

def get_prv_cd():
    qry = Area_Info.select(Area_Info.sig_cd, Area_Info.sig_nm).where(Area_Info.sig_lvl == 1)

    return [x.sig_cd for x in qry]

def get_sgg_cd_from_prv_cd(prv_cd):
    """광역단체 코드 하위 모든 읍면동 코드를 다 들고 온다."""
    qry = Area_Info.select(Area_Info.sig_cd).where(fn.Substr(Area_Info.sig_cd, 1, 2) == prv_cd, Area_Info.sig_lvl == 2)

    return [x.sig_cd for x in qry]

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
        header[e.party] = election_type[et] + "_" + e.party
        #header[e.name] = e.party.encode('utf8')
        votes[e.party]  = str(e.vsum)
        rvotes[e.party] = "%.4f" % (float(e.vsum) / float(vote_sum))

    return { 'header' : header,
             'vote' : votes,
             'ratio' : rvotes } 

def is_list_same(list1, list2):
    if len(list1) != len(list2):
        return False

    for i in range(len(list1)):
        if list1[i] != list2[i]:
            return False

    return True

# select distinct(c.party) from election_info as e, candidate_info as c where e.candidate_id = c.id and e.elec_type like '시도지사';
#새누리당
#새정치민주연합
#통합진보당
#정의당
#무소속
#노동당
#새정치당

position_2 = {
    0:u"sig_cd",
    1:u"권역",
    2:u"시군구",
    3:u"읍면동",
    4:u"새누리당",
    5:u"새정치민주연합",
    6:u"통합진보당",
    7:u"정의당",
    8:u"무소속",
    9:u"노동당",
    10:u"새정치당",
}

#광역비례
#새누리당
#새정치민주연합
#통합진보당
#정의당
#노동당
#녹색당
#새정치당
#새정치
#통합
#공화당
#국제녹색당
#한나라당

position_3 = {
    0:u"sig_cd",
    1:u"권역",
    2:u"시군구",
    3:u"읍면동",
    4:u"새누리당",
    5:u"새정치민주연합",
    6:u"통합진보당",
    7:u"정의당",
    8:u"노동당",
    9:u"녹색당",
    10:u"새정치당",
    11:u"새정치",
    12:u"통합",
    13:u"공화당",
    14:u"국제녹색당",
    15:u"한나라당",
}

def rev_lookup(party_name, sel):
    if sel == 2:
        for i in position_2.keys():
            if position_2[i] == party_name:
                return i

    if sel == 3:
        for i in position_3.keys():
            if position_3[i] == party_name:
                return i

    print "ERROR"
    return -1

book = Workbook()
sheet = book.add_sheet(u"광역비례")
row_count = 0
for i in range(len(position_3)):
    sheet.write(row_count, i, position_3[i])

for prv in Area_Info.select(Area_Info.sig_cd, Area_Info.sig_nm).where(Area_Info.sig_lvl == 1):
    print "%s (%s)" % (prv.sig_nm, prv.sig_cd)
    print "=========================="
    for sgg in Area_Info.select(Area_Info.sig_cd, Area_Info.sig_nm).where(Area_Info.sig_lvl == 2, fn.Substr(Area_Info.sig_cd, 1, 2) == prv.sig_cd):
        print "%s (%s)" % (sgg.sig_nm, sgg.sig_cd)
        print "--------------------------"

        emd_cds = get_emd_cd_from_sgg_cd(sgg.sig_cd)
        for emd_cd in emd_cds:
            row_count = row_count + 1

            emd_info = get_area_full_info_from_emd(emd_cd)
            vote_info1 = get_standard_info_from_emd(emd_cd, election_type_reverse[u'광역비례']);

            colnum = 0
            for i in [emd_cd,] + emd_info:
                sheet.write(row_count, colnum, i)
                colnum = colnum + 1
            
            for i in vote_info1['ratio'].keys(): # keys are party names
                sheet.write(row_count, rev_lookup(i,election_type_reverse[u'광역비례']), vote_info1['ratio'][i])
            
        sheet.flush_row_data()
        book.save('20140730_광역비례.xls')

