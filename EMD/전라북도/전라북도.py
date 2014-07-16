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

DEBUG_POINT1 = 1
DEBUG_POINT2 = 0
DB_ACCESS_MODE = 0
prv_name = u"전라북도"
election_name = u"201406지방선거"


print "DEBUG_POINT1 = %d" % DEBUG_POINT1
print "DEBUG_POINT2 = %d" % DEBUG_POINT2
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
    #print "candidate_id = %d" % candidate_id
    #print "count_type = %s" % total_type
    #print "vote = %d" % vote

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

def save_candidate_info(election_name, election_type, election_level, column_offset, prv_name, sgg_name, precinct_name, name, party):
    #print [x.encode("utf8") for x in (election_name, election_type, unicode(election_level), unicode(column_offset), prv_name, sgg_name, precinct_name, name, party)]
    #print "#######"
    #print election_name.encode("utf8")
    #print election_type.encode("utf8")
    #print election_level
    #print column_offset
    #print prv_name.encode("utf8")
    #if sgg_name is not None:
    #    print sgg_name.encode("utf8")
    #print precinct_name.encode("utf8")
    #print name.encode("utf8")
    #print party.encode("utf8")
    #print "#######"
    #print "%s %s %d %d %s %s %s %s %s" % [x.encode("utf8") for x in (election_name, election_type, unicode(election_level), unicode(column_offset), prv_name, sgg_name, precinct_name, name, party)]
    #print [type(x) for x in (election_name, election_type, unicode(election_level), unicode(column_offset), prv_name, sgg_name, precinct_name, name, party)]

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

        base_filename = file_in_dir[:file_in_dir.find(".")]
        sgg_name = u""

        info_from_filename = base_filename.split("-")
        election_type = info_from_filename[1][3:]  # 01_시도지사선거 이런 식으로 되어 있음.

        if len(info_from_filename) == 3 and not (election_type == u'기초의원비례대표'):
            # 광역레벨의 경우
            sgg_name      = "" # will be imputed in the actual excel sheet
            precinct_name = info_from_filename[2]
            election_level = 1
            column_offset = 0 # 전라남도는 첫번째 컬럼이 시군구
        elif len(info_from_filename) == 3:
            # 기초의원비례대표의 경우
            sgg_name      = info_from_filename[2] # 고흥군 이런 식
            precinct_name = sgg_name # 같은 선거구
            election_level = 2
            column_offset = -1
        elif len(info_from_filename) == 4:
            sgg_name      = info_from_filename[2] # 읍면동개표자료(전남)-05_구시군의원-화순군-화순군나선거구
            precinct_name = info_from_filename[3] #
            election_level = 2
            column_offset = -1
            if election_type == u'구시군장':
                sgg_name = precinct_name
        else:
            print "Something is wrong with encoding or filename: %s" % base_filename.encode("utf8")
            raw_input()

        # DEBUG-POINT1
        if DEBUG_POINT1: 
            print "%s -- %s -- %s" % (base_filename.encode("utf8"), sgg_name.encode("utf8"), precinct_name.encode("utf8"))
            raw_input()
            continue;

        election_types[election_type] = 1; # dictionary (legacy)

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

            #if (sheet.name != "Sheet1") and election_level == 1:
            #    # this means it is 광역레벨
            #    sgg_name = sheet.name 

            for rownum in xrange(sh.nrows):
                # this should also clean up all commas, and make utf-8
                values = map(just_all_utf8_str, sh.row_values(rownum))
                if DEBUG_POINT2:
                    print "::".join(values)
                    #raw_input()

                if rownum <= 3: # this is the header
                    # this is the header, and should be processed to add 의원 info
                    if values[0] == "" and sheet_count < 2 and rownum == 3: # 후보자를 중복해서 추가하지 말자.
                        # 후보자 이름$ 및 만약 CR이 있으면 당명도 있음.
                        index = 0
                        for cn in values[5+column_offset:-3]:
                            cn = cn.decode("utf8")
                            if len(cn.split("\n")) > 1:
                                [party, name] = cn.split("\n")
                            else:
                                if election_type == u"광역의원비례대표" or election_type == u'기초의원비례대표':
                                    party = cn
                                    name  = cn
                                else:
                                    party = ""
                                    name = cn

                            if election_level == 1: #광역레벨일 경우에 그렇게 써줘야한다.
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
                    else: # useless header (1-2)
                        "this is useless header (1-2)"
                else: 
                    # 이제 헤더가 아니기때문에 확인해야한다.
                    if column_offset >= 0: # 광역레벨인 경우에는 첫 컬럼이 시군구 선관위명이다.
                        sgg_name = values[0].decode("utf8").replace("\n","") # sometimes they have \n
                        if (sgg_name == prv_name):
                            #경상남도의 경우 광역레벨의 합계도 있는데, 이건 걍 빼자.
                            continue
                    else:
                        "otherwise, you have already sgg_name from filename"
    
                    column1 = values[1+column_offset].decode("utf8")
    
                    if column1 == u"합계" or column1 == u"관외사전투표" or column1 == u"거소우편투표" or column1 == u"잘못 투입·구분된 투표지":
                        # 이 경우에는 시군구 레벨의 자료들로 구성되어 있으므로 해당 sig_cd를 찾아서 입력한다.
                        # election_level은 전체 선거구의 level임을 주의하자.
                        votes = map(int, values[5+column_offset:-3])
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
                    elif column1.find("/") == "-1": # 읍면동이 두 번째 컬럼이다
                        emd_name              = column1 # 행정동이름 (precinct_name 은 선거구 이름)
                        total_type            = values[2+column_offset].decode("utf8") # 소계/관내/일반
                        precinct_population   = int(values[3+column_offset])  # 유권자수
                        precinct_votetotal    = int(values[4+column_offset])  # 투표수
                        precinct_disqualified = int(values[-2]) # 무효 
    
                        # only do the ERROR once.
                        if error_emd_name == emd_name and error_sgg_name == sgg_name and error_flag:
                            continue
                        else:
                            error_emd_name = u""
                            error_sgg_name = u""
                            error_flag = False
    
                        if int(values[-3]) + precinct_disqualified != precinct_votetotal:
                            print "No match!!!! %s" % (emd_name)
    
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

                        votes = map(int, values[5+column_offset:-3])
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
                    else:
                        "some empty rows probably last line problem"
