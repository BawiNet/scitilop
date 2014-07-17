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

prv_name = u"경기도"
election_name = u"201406지방선거"
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

    if sgg_name == u'여주시':
        sgg_name = u'여주군' # 2013년 9월 23일 여주시 승격이 SGIS에는 들어있지 않아 강제 match.
    
    for area in Area_Info.select().where(fn.Substr(Area_Info.sig_cd, 1, 2) == lvl1_cd, Area_Info.sig_nm == sgg_name): 
        lvl2_cd = area.sig_cd
    
    return lvl2_cd

def get_sigcd_from_prv_sgg_emd_name(prv_name, sgg_name, emd_name):
    # we have sgg_name and emd_name for each EMD or SGG level election result
    # to avoid any redundant same name problem, start from the highest level
    lvl2_cd = get_sigcd_from_prv_sgg_name(prv_name, sgg_name)
    #print "get_sigcd_from_prv_sgg_emd_name : %s" % emd_name

    lvl3_cd = None
    
    if sgg_name == u'수원시팔달구' and emd_name == u'서둔동':
        sgg_name = u'수원시권선구' # 선거구만 권선구에서 팔달구로 편입됨
        lvl2_cd = get_sigcd_from_prv_sgg_name(prv_name, sgg_name)

    if sgg_name == u'시흥시' and emd_name == u'월곶동':
        emd_name = u'군자동' # 월곶동은 군자동에서 분동됨.

    if sgg_name == u'시흥시' and emd_name == u'장곡동':
        emd_name = u'연성동' # 장곡동은 연성동에서 분동됨.

    if sgg_name == u'파주시' and emd_name == u'진동면':
        # SGIS에서 해당 데이터를 뽑을 수가 없음. 민통선 이북이라서?
        # 가까운 군내면에 산입하겠음.
        emd_name = u'군내면'

    if (sgg_name == u'여주군' or sgg_name == u'여주시') and emd_name == u'가남읍':
        emd_name = u'여주읍' # 2013년 9월 23일 여주시 승격이 SGIS에는 들어있지 않아 강제 match.

    if (sgg_name == u'여주군' or sgg_name == u'여주시') and emd_name == u'여흥동':
        emd_name = u'여주읍' # 2013년 9월 23일 여주읍이 폐지되면서 3개동으로 분동됨.

    if (sgg_name == u'여주군' or sgg_name == u'여주시') and emd_name == u'중앙동':
        emd_name = u'여주읍' # 2013년 9월 23일 여주읍 폐지 (시승격) 3개동으로 분동.

    if (sgg_name == u'여주군' or sgg_name == u'여주시') and emd_name == u'오학동':
        emd_name = u'여주읍' # 2013년 9월 23일 여주읍 폐지 (시승격) 3개동으로 분동.

    if sgg_name == u'용인시기흥구' and emd_name == u'상현2동':
        sgg_name = u'용인시수지구'
        lvl2_cd = get_sigcd_from_prv_sgg_name(prv_name, sgg_name)

    if sgg_name == u'김포시' and emd_name == u'구래동':
        emd_name = u'김포2동' # 2013년 10월 28일 김포시 김포2동으로부터 분동 


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
    e.save()
        
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

        if not m.group(1) is None:
            # "xlsx file" 
            s1_idx = file_in_dir.rfind("-")
            s2_idx = file_in_dir.rfind(".xlsx")
            election_type = file_in_dir[s1_idx+1:s2_idx]
            precinct_name = election_type
        else:
            # you could have used split method -_-
            s1_idx = file_in_dir.find("-")
            s2_idx = file_in_dir[s1_idx+1:].find("-") + s1_idx + 1
            s3_idx = file_in_dir[s2_idx+1:].find("-") + s2_idx + 1
            s4_idx = file_in_dir.rfind(".")
            election_type = file_in_dir[s1_idx+1:s2_idx] # 선거의 종류
            if (s3_idx == s2_idx): # 선거구 (없는 경우도 존재)
                sgg_name = file_in_dir[s2_idx+1:s4_idx] 
                precinct_name = sgg_name # 없는 경우에는 시군구 이름으로 대체
            else:
                precinct_name = file_in_dir[s3_idx+1:s4_idx] 
                sgg_name      = file_in_dir[s2_idx+1:s3_idx] # 시군구 선관위명

            if election_type == u"구시군의원" or election_type == u"시도의원":
                sgg_name = sgg_name[2:]

            if (election_type == u"구시군의장" or election_type == u"기초비례의원") and precinct_name != u"":
                sgg_name = precinct_name
                #고양시 덕양구 같은 경우엔 마지막 선거구가 의미가 시군구가 됨.

        election_types[election_type] = 1; # dictionary
        wb = open_workbook(file_in_dir)
        candidate_id = range(100) # just making an array (I don't know what to do)

        error_flag = False
        error_emd_name = u""
        error_sgg_name = u""

        if election_type == u"경기도교육감" or election_type == u"경기도지사" or election_type == u"광역비례의원":
            column_offset = 0
            election_level = 1
        else: # 광역선거가 아닌 경우
            # 이 경우에는 시군구가 파일이기때문에, column이 하나씩 밀린다.
            election_level = 2
            column_offset = -1

        # main parsing routine
        sh = wb.sheet_by_name('Sheet1')

        for rownum in xrange(sh.nrows):
            # this should also clean up all commas, and make utf-8
            values = map(just_all_utf8_str, sh.row_values(rownum))
            if rownum <= 3: # this is the header
                # this is the header, and should be processed to add 의원 info
                if values[0] == "": 
                    # 후보자 이름$ 및 만약 CR이 있으면 당명도 있음.
                    index = 0
                    for cn in values[5+column_offset:-3]:
                        cn = cn.decode("utf8")
                        if len(cn.split("\n")) > 1:
                            [party, name] = cn.split("\n")
                        else:
                            if election_type == u"광역비례의원" or election_type == u"기초비례의원":
                                party = cn
                                name  = cn
                            else:
                                party = ""
                                name = cn

                        candidate = Candidate_Info()
                        candidate.election = election_name
                        candidate.elec_type = election_type
                        candidate.lvl       = election_level
                        if (column_offset >= 0):
                            candidate.sig_cd    = get_sigcd_from_prv_name(prv_name)
                        else: # 기초선거의 경우에는 후보자의 선거구는 최소한 시군구 또는 그 아래 (하지만 읍면동 위)까지 내려간다.
                            candidate.sig_cd    = get_sigcd_from_prv_sgg_name(prv_name, sgg_name)
                        candidate.sig_id    = get_sigid_from_sigcd(candidate.sig_cd)
                        candidate.precinct  = precinct_name
                        candidate.name      = name
                        candidate.party     = party
                        candidate.save()

                        candidate_id[index] = candidate.id
                        index = index + 1
                else: # useless header (1-2)
                    "this is useless header (1-2)"
            else: 
                # 이제 헤더가 아니기때문에 확인해야한다.
                if column_offset >= 0: # 광역레벨인 경우에는 첫 컬럼이 시군구 선관위명이다.
                    sgg_name = values[0].decode("utf8")
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
                else: # 읍면동이 두 번째 컬럼이다
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

                    votes = map(int, values[5+column_offset:-3])
                    for ind_vote in range(len(votes)):
                        test = get_sigcd_from_prv_sgg_emd_name(prv_name, sgg_name, emd_name)
                        if test is None:
                            print "ERROR: %s %s %s not exist in the table" % (prv_name, sgg_name, emd_name)
                            error_emd_name = emd_name
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
                                emd_name,
                                precinct_name,
                                candidate_id[ind_vote],
                                total_type,
                                votes[ind_vote]
                            )
