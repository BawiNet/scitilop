#!/usr/bin/python
# -*- coding: utf-8 -*-

from mmap import mmap, ACCESS_READ
from xlrd import open_workbook
import os
import re
import csv
import csv, codecs, cStringIO
import unicodedata
from peewee import *

DEBUG_POINT1 = 0 # 파일명 파싱이 잘 되는가
DEBUG_POINT2 = 0 # 개별 row를 출력하도록 한다.
DEBUG_POINT3 = 0 # 후보자 save 
DEBUG_POINT4 = 0 # 개별 선거결과 save 
DEBUG_HEADER = 0 # 헤더의 경우 다음 줄과 함께 봄
DEBUG_EACHFILE = 0 # 각 파일별로 raw_input를 받음 (DEBUG_POINT2와 함께 쓸 것)
DEBUG_INPUT  = 0 # additional option for DEBUG_POINT3 & DEBUG_POINT4
DB_ACCESS_MODE = 0
prv_name = u"광주광역시"
election_name = u"201406지방선거"


print "DEBUG_POINT1 = %d" % DEBUG_POINT1
print "DEBUG_POINT2 = %d" % DEBUG_POINT2
print "DEBUG_POINT3 = %d" % DEBUG_POINT3
print "DEBUG_POINT4 = %d" % DEBUG_POINT4
print "DEBUG_HEADER = %d" % DEBUG_HEADER
print "DEBUG_EACHFILE = %d" % DEBUG_EACHFILE
print "DB_ACCESS_MODE = %d" % DB_ACCESS_MODE
print "prv_name = %s || election_name = %s" % (prv_name.encode("utf8"), election_name.encode("utf8"))

#
# DATABASE
#

db = SqliteDatabase('../201406_EMD.sqlite3')

class EMDDBModel(Model):
    class Meta:
        database = db

class Area_Info(EMDDBModel):
    id        = IntegerField()
    sig_lvl   = TextField()
    sig_cd    = TextField()
    sig_nm    = TextField()
    prev_id   = IntegerField()
    next_id   = IntegerField()
    parent_id = IntegerField()  

class Candidate_Info(EMDDBModel):
    id          = IntegerField()

    # about the election
    election    = TextField()      # which election
    elec_type   = TextField()      # electiontype
    lvl         = TextField()      # level in which candidate is
    sig_cd      = TextField()      # the accompanying area (foreign key to area_info)
    sig_id      = IntegerField()   # the foreighkey
    precinct    = TextField()      # precinct name can be unique

    # about the candidate
    name        = TextField()      # candidate name
    party       = TextField()      # party affiliation

# make tables very simple although this makes a lot of redundancies.
class Election_Info(EMDDBModel):
    # 중요! 분동된 행정동들을 산입한 경우가 있기때문에 selection이 sgg_name, emd_name에 따라 여러 row이 selection될 수 있다.
    id           = IntegerField()  
    # about the election
    election    = TextField()      # which election
    elec_type   = TextField()      # electiontype
    lvl         = TextField()      # level in which count is. (0: presidential) 
    sig_cd      = TextField()      # the accompanying area (foreign key to area_info)
    sig_id      = IntegerField()   # the foreighkey
    precinct    = TextField()      # precinct name can be unique
    # about the election result
    candidate_id= IntegerField()   # Link to Candidate_info
    count_type   = TextField()     # 소계 / 관외 / 관내 / 우편 / 잘못 투입
    count        = IntegerField()  # the actual count
    # 잘못투입/구분된 투표지는 count_type, 선거구(precinct level~시군구)로 보인다.

db.connect()

def get_sigcd_from_prv_name(prv_name):
    lvl1_cd = Area_Info.get(Area_Info.sig_nm == prv_name).sig_cd
    #print "get_sigcd_from_prv_name : %s" % prv_name
    
    return lvl1_cd

def get_sigcd_from_prv_sgg_name(prv_name, sgg_name):
    lvl1_cd = get_sigcd_from_prv_name(prv_name)
    #print "get_sigcd_from_prv_sgg_name : %s" % sgg_name

    lvl2_cd = None

    for area in Area_Info.select().where(fn.Substr(Area_Info.sig_cd, 1, 2) == lvl1_cd, Area_Info.sig_nm == sgg_name): 
        lvl2_cd = area.sig_cd

    if lvl2_cd is None:
        print "ERROR: get_sigcd_from_prv_sgg_name : %s %s" % (sgg_name, lvl1_cd)
    
    return lvl2_cd

def get_sigcd_from_prv_sgg_emd_name(prv_name, sgg_name, emd_name):
    # we have sgg_name and emd_name for each EMD or SGG level election result
    # to avoid any redundant same name problem, start from the highest level
    lvl2_cd = get_sigcd_from_prv_sgg_name(prv_name, sgg_name)
    #print "get_sigcd_from_prv_sgg_emd_name : %s" % emd_name

#    m = re.compile(u"제([1-9]{1}동)$")
#    if m.search(emd_name):
#        emd_name = emd_name[:emd_name.rfind(u"제")] + emd_name[emd_name.rfind(u"제")+1:]
#        #print emd_name.encode("utf8")
#        #raw_input() 

    lvl3_cd = None

    for area in Area_Info.select().where(fn.Substr(Area_Info.sig_cd, 1, 5) == lvl2_cd, Area_Info.sig_nm == emd_name):
        lvl3_cd = area.sig_cd

    return lvl3_cd

def get_sigid_from_sigcd(sig_cd):
    sig_id = 0
    for area in Area_Info.select().where(Area_Info.sig_cd == sig_cd):
        sig_id = area.id

    return sig_id

def save_election_info(election_name, election_type, election_level, prv_name, sgg_name, emd_name, precinct_name, candidate_id, total_type, vote):
    e = Election_Info()
    e.election     = election_name
    e.elec_type    = election_type
    e.lvl          = election_level

    if (emd_name is None):
        e.sig_cd   = get_sigcd_from_prv_sgg_name(prv_name, sgg_name)
    else:
        e.sig_cd   = get_sigcd_from_prv_sgg_emd_name(prv_name, sgg_name, emd_name)
    e.sig_id       = get_sigid_from_sigcd(e.sig_cd)
    e.precinct     = precinct_name
    e.candidate_id = candidate_id
    e.count_type   = total_type
    e.count        = vote

    if DB_ACCESS_MODE:
        e.save()

    if DEBUG_POINT4:
        print "election save: sgg_name = %s sig_cd = %s count_type = %s count = %d" % (
            sgg_name.encode("utf8"), e.sig_cd.encode("utf8"), total_type.encode("utf8"), vote
        )

def save_candidate_info(election_name, election_type, election_level, column_offset, prv_name, sgg_name, precinct_name, name, party):
    candidate = Candidate_Info()
    candidate.election = election_name
    candidate.elec_type = election_type
    candidate.lvl       = election_level
    if sgg_name is None: # 광역레벨의 경우 후보자의 sgg_name을 안 넘겨서 확인한다.
        candidate.sig_cd    = get_sigcd_from_prv_name(prv_name)
    else: # 기초선거의 경우에는 후보자의 선거구는 최소한 시군구 또는 그 아래 (하지만 읍면동 위)까지 내려간다.
        candidate.sig_cd    = get_sigcd_from_prv_sgg_name(prv_name, sgg_name)
    candidate.sig_id    = get_sigid_from_sigcd(candidate.sig_cd)
    candidate.precinct  = precinct_name
    candidate.name      = name
    candidate.party     = party
   
    if DEBUG_POINT3:
        print "candidate save: party = %s name = %s" % (party.encode("utf8"), name.encode("utf8"))
    
    if DB_ACCESS_MODE: 
        candidate.save()
        return candidate.id

    return 0
        
#
# FLOAT TO INT
#
def just_all_utf8_str(x):
    if type(x) == type(3.0):
        return str(int(x)).encode("utf-8")

    if type(x) == type(3):
        return str(x).encode("utf-8")

    return x.replace(",","").encode("utf-8")


def just_encode_utf8_for_str(x):
    if type(x) == type(3.0):
        return int(x)

    if type(x) == type(3):
        return x
    return x.encode("utf-8")

# https://docs.python.org/2/library/csv.html#csv-examples
class UnicodeWriter:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow(map(just_encode_utf8_for_str,row))
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

#
# MAIN
#

election_types = {}

files_in_dir = os.listdir('.')
for file_in_dir in files_in_dir:
    # http://stackoverflow.com/questions/9757843/unicode-encoding-for-filesystem-in-mac-os-x-not-correct-in-python
    # it is recommended to handle only unicode data in Python 2.X and only encode when necessary
    file_in_dir = unicodedata.normalize('NFC', unicode(file_in_dir, 'utf-8'))   

    excelfile = re.compile(r".xls(x)*")
    m = excelfile.search(file_in_dir)
    if m:
        print "OPENING %s....." % file_in_dir
        print

        base_filename = file_in_dir[:file_in_dir.find(".")]
        sgg_name = u""

        info_from_filename = base_filename.split("-")
        election_type = info_from_filename[0][3:]  

        if len(info_from_filename) == 2 and not (election_type == u'기초비례' or election_type == u'구시군장'):
            # 광역레벨의 경우
            sgg_name      = "" # will be imputed in the actual excel sheet
            precinct_name = info_from_filename[1]
            election_level = 1
            column_offset = -1 # 광주광역시는 광역도 쉬트별로 되어 있다.
        elif len(info_from_filename) == 2: 
            # 기초의원비례대표 또는 구시군장.
            sgg_name = info_from_filename[1][3:] # 01_동구 이런 식 
            precinct_name = sgg_name # 같은 선거구
            election_level = 2
            column_offset = -1

            if sgg_name == u"창원시": #창원시의 경우에는 칼럼이 하나 더 들어간다.
                column_offset = 0
                sgg_name = u"" # 이건 첫번째 열에서 뽑아야한다.
                # precinct_name는 "창원시"라고 갖고 있어서 추후에 확인할 것이다.
        elif len(info_from_filename) == 3:
            sgg_name      = info_from_filename[1][3:]  # 03_시도의원-01_동구-동구제1선거구
            precinct_name = info_from_filename[2]      #
            election_level = 2
            column_offset = -1

        else:
            print "Something is wrong with encoding or filename: %s" % base_filename.encode("utf8")
            raw_input()

        # DEBUG-POINT1
        if DEBUG_POINT1: 
            print "%s -- %s -- %s" % (base_filename.encode("utf8"), sgg_name.encode("utf8"), precinct_name.encode("utf8"))
            raw_input()
            continue;

        election_types[election_type] = 1; # dictionary (legacy)
        #if election_type != u'교육감':
        #    continue

        wb = open_workbook(file_in_dir)
        candidate_id = range(100) # just making an array (I don't know what to do)

        error_flag = False
        error_emd_name = u""
        error_sgg_name = u""

        # main parsing routine
        # 서울특별시의 경우 광역레벨은 구별 데이터가 쉬트별로 저장되어 있다-_-;;;
        # 따라서 처음만 후보 정보를 저장하고, 각 sheet이름에서 sgg_name을 뽑아야한다.
        #for s in wb.sheets():
        #    print 'Sheet:', s.name
        #continue;

        sheet_count = 0
        for sheet in wb.sheets():
            sheet_count = sheet_count + 1
            sh = wb.sheet_by_name(sheet.name)

            if (sheet.name != "Sheet1") and election_level == 1:
                # this means it is 광역레벨
                sgg_name = sheet.name 

            # TODO
            # 경우에 따라서 header가 4줄이기도 5줄이기도 하다.
            header_flag = True
            split_flag = False
            bigo_check_flag = False
            bigo_offset = -1
            candidate_size = 0
            for rownum in xrange(sh.nrows):
                # this should also clean up all commas, and make utf-8
                values = map(just_all_utf8_str, sh.row_values(rownum))
                if DEBUG_POINT2:
                    print "row" + str(rownum) + "::".join(values)
                    #raw_input()

                if header_flag: 
                    # 이건 만에 하나 당명이 쪼개져있는 경우 참조하기 위해서
                    values2 = map(just_all_utf8_str, sh.row_values(rownum+1))

                    if DEBUG_HEADER:
                        print "row#" + str(rownum+1) + "::".join(values2)
                    # this is the header, and should be processed to add 의원 info

                    # "비고"가 있는 경우가 있고 없는 경우가 있다.
                    # 이를 확인하기 위해서, 첫번째 헤더를 마주칠 때 (두 번째 컬럼이 채워져있을 때)
                    if values[3+column_offset] != "" and not bigo_check_flag:
                        # 비고를 체크하기 위한 줄이다.
                        bigo_check_flag = True

                        if values[-1].decode('utf8').replace(" ","")[:2] == u"비고":
                            if DEBUG_POINT3:
                                print "비고있음"
                            bigo_offset = -1
                        elif values[-1].decode('utf8').replace(" ","")[:2] == u"" and values[-2].decode('utf8').replace(" ","")[:2] == u"비고":
                            if DEBUG_POINT3:
                                print "비고있고 공백도있음"
                            bigo_offset = -2
                        elif values[-1].decode('utf8').replace(" ","")[:2] == u"":
                            if DEBUG_POINT3:
                                print "공백이 하나 있음"
                            bigo_offset = -1
                        else:
                            if DEBUG_POINT3:
                                print "비고없음"
                            bigo_offset = 0
                    # 경우에 따라선 컬럼 자체가 추가되어 있어서 더 빼야하는 경우도 있다.
                    elif values[3+column_offset] != "" and values[-1].decode('utf8').replace(" ","")[:2] == "":
                        if not bigo_check_flag:
                            if DEBUG_POINT3:
                                print "공백이 있음."
                   
                    if (values[3+column_offset] == "" ) and values[6+column_offset][:4] != "": 
                        #광주광역시같이 쉬트별로 후보자가 반복되는 경우에는 한 번만 입력하도록 해야한다.
                        if split_flag:
                            split_flag = False
                            header_flag = False
                            continue
                        index = 0
                        for cn in values[5+column_offset:-3+bigo_offset]:
                            cn = cn.decode("utf8")
                            if cn == "":  #공백으로 후보자란이 뒤에 붙는 경우가 있다.
                                break
                            if len(cn.split("\n")) > 1 and not split_flag:
                                temp = cn.split("\n")
                                name  = temp[-1].replace(" ","") # 가끔씩 \n이 여러 번 쳐진 경우가 있는 듯.
                                party = "".join(temp[:-1]).replace(" ","") # 이것도 지저분하게 공백 붙는 경우 있음.
                            else: #교육감선거, 비례대표선거
                                if election_type == u"광역비례" or election_type == u'기초비례':
                                    party = cn.replace("\n", "")
                                    name  = party
                                else:
                                    if (cn.find(u'당') >= 0 or cn.find(u'무소속') >= 0) or split_flag:
                                        # 당명만 있는 경우다
                                        # !#@%)(!#&*%#*^& 진짜 이 짓을 하는 내가 바보.
                                        party = cn.replace("\n","").replace(" ", "") # 이것도 지저분하게 공백 붙는 경우 있음.
                                        name = values2[5+column_offset:-3+bigo_offset][index].decode("utf8").replace(" ","")
                                        split_flag = True
                                    else:
                                        party = ""
                                        name = cn.replace(" ","")

                            if election_level == 1 or election_type == u"기초비례": #광역레벨일 경우에 그렇게 써줘야한다.
                                if sheet_count == 1: # 저장만 안 해야한다.
                                    # 기초비례대표의원의 경우 광역레벨로 저장하자.
                                    candidate_id[index] = save_candidate_info(
                                        election_name, 
                                        election_type, 
                                        election_level, 
                                        column_offset, 
                                        prv_name, 
                                        None, #sgg_name 
                                        precinct_name, 
                                        name, 
                                        party
                                    )
                            else:
                                candidate_id[index] = save_candidate_info(
                                    election_name, 
                                    election_type, 
                                    election_level, 
                                    column_offset, 
                                    prv_name, 
                                    sgg_name, 
                                    precinct_name, 
                                    name, 
                                    party
                                )
    
                            index = index + 1
                        candidate_size = index
                        if DEBUG_POINT3:
                            print "candidate_size = %d" % candidate_size
                        if DEBUG_POINT3 and DEBUG_INPUT:
                            raw_input()
                        if DEBUG_POINT3 and candidate_size == 0:
                            raw_input()

                        if split_flag:
                            "이 flag는 다음 줄에서 해제한다."
                        else:
                            header_flag = False # 후보자 정보를 입력한 다음부턴 헤더가 아니다.
                    else: # useless header (1-3)
                        "this is useless header (1-3)"
                else: 
                    if not bigo_check_flag:
                        print "DID NOT CHECKED BIGO!"
                    # 이제 헤더가 아니기때문에 확인해야한다.
                    if column_offset >= 0 and (election_level == 1 or election_type == u"기초비례"): 
                        # 광역레벨도 읍면동부터 시작해서 -1이기때문에 여기 안 걸린다.
                        sgg_name = values[0].decode("utf8").replace("\n","") # sometimes they have \n
                        if (election_type == u"기초비례"):
                            precinct_name = sgg_name
                        if (sgg_name == prv_name):
                            #광역레벨의 합계도 있는데, 이건 걍 빼자.
                            continue
                    else:
                        "otherwise, you have already sgg_name from filename"
    
                    column1 = values[1+column_offset].decode("utf8").replace(" ","").replace("\n","")
                    if column1 == u"잘못투입된투표지":
                        column1 = u"잘못투입·구분된투표지"
    
                    if column1 == u"합계" or column1 == u"관외사전투표" or column1 == u"거소우편투표" or column1 == u"잘못투입·구분된투표지":
                        # 이 경우에는 시군구 레벨의 자료들로 구성되어 있으므로 해당 sig_cd를 찾아서 입력한다.
                        # election_level은 전체 선거구의 level임을 주의하자.
                        votes = map(int, values[5+column_offset:-3+bigo_offset][:candidate_size])
                        for ind_vote in range(len(votes)):
                            # 에러 메시지 생략. 어차피 읍면동 수준에서 걸릴 것임. 
                            save_election_info(
                                election_name,
                                election_type,
                                election_level,
                                prv_name,
                                sgg_name,
                                None, # 시군구레벨이다.
                                precinct_name,
                                candidate_id[ind_vote],
                                column1, # 합계, 관외사전투표, 거소우편투표, 잘못 투입.구분된 투표지 모두 포함됨.
                                votes[ind_vote]
                            )
                        if DEBUG_POINT4 and DEBUG_INPUT:
                            raw_input()
                    elif (column1.find("/") == -1 and column1.find(u"개표진행") == -1 and column1 != "" and 
                          column1 != u"읍면동명" and column1.find("[") == -1): 
                        # 헤더가 반복되는 경우가 있는데, 그 경우의 수를 다 제외하고 읍면동을 분석함.
                        # 읍면동이 두 번째 컬럼이다
                        emd_name              = column1 # 행정동이름 (precinct_name 은 선거구 이름)
                        total_type            = values[2+column_offset].decode("utf8") # 소계/관내/일반
                        precinct_population   = int(values[3+column_offset])  # 유권자수
                        precinct_votetotal    = int(values[4+column_offset])  # 투표수
                        precinct_disqualified = int(values[-2+bigo_offset]) # 무효 

                        if total_type == "": #소계가 안 되어 있는 경우가 있다.
                            total_type = u"소계"
    
                        # only do the ERROR once.
                        if error_emd_name == emd_name and error_sgg_name == sgg_name and error_flag:
                            continue
                        else:
                            error_emd_name = u""
                            error_sgg_name = u""
                            error_flag = False
    
                        if int(values[-3+bigo_offset]) + precinct_disqualified != precinct_votetotal:
                            print "No match!!!! %s" % (emd_name)
   
                        # 나주시 빛가람동은 산포면과 금천면의 일부 리들을 떼어서 만든 것이다.
                        # 따라서 산포면과 금천면에 각각 반절씩 집어넣자.

                        # 통합동의 경우에는 그 수만큼 나눠서 더해주자. 이 경우 반내림을 하자.
                        if (sgg_name == u"진주시" and emd_name == u"천전동"):
                            emds = [u'망경동', u'강남동', u'칠암동']
                        elif (sgg_name == u"진주시" and emd_name == u"성북동"):
                            emds = [u'성지동', u'봉안동', u'신안동']
                        elif (sgg_name == u"진주시" and emd_name == u"상봉동"):
                            emds = [u'상봉동동', u'상봉서동']
                        elif (sgg_name == u"진주시" and emd_name == u"충무공동"):
                            emds = [u'문산읍', u'금산면'] # 호탄동은 존재하지 않는다.
                        else:
                            emds = [emd_name]
#                        emds = [emd_name]

                        votes = map(int, values[5+column_offset:-3+bigo_offset][:candidate_size])
                        votes = [x/len(emds) for x in votes] # 통합된 동들의 경우 예전 동들에서 나눈다.
                        for ind_vote in range(len(votes)):
                            for emd in emds:
                                test = get_sigcd_from_prv_sgg_emd_name(prv_name, sgg_name, emd)
                                if test is None:
                                    print "ERROR: %s %s %s not exist in the table" % (prv_name, sgg_name, emd)
                                    error_emd_name = emd
                                    error_sgg_name = sgg_name
                                    error_flag = True
                                    break;
                                else:
                                    save_election_info(
                                        election_name,
                                        election_type,
                                        election_level,
                                        prv_name,
                                        sgg_name,
                                        emd,
                                        precinct_name,
                                        candidate_id[ind_vote],
                                        total_type,
                                        votes[ind_vote]
                                    )
                            if error_flag:
                                break # break one more loop
                        if DEBUG_POINT4 and DEBUG_INPUT:
                            raw_input()
                    else:
                        "some empty rows probably last line problem"
        if DEBUG_EACHFILE:
            raw_input()
