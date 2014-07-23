#!/usr/bin/env python
# _*_ coding: utf-8 _*_

from peewee import *

db = SqliteDatabase('201406_EMD.sqlite3')

class EMDDBModel(Model):
    class Meta:
        database = db

class Area_Info(EMDDBModel):
    id        = IntegerField(primary_key=True)
    sig_lvl   = TextField()
    sig_cd    = TextField()
    sig_nm    = TextField()
    prev_id   = IntegerField()
    next_id   = IntegerField()
    parent_id = IntegerField()

class Candidate_Info(EMDDBModel):
    id          = IntegerField(primary_key=True)

    # about the election
    election    = TextField()      # which election
    elec_type   = TextField()      # electiontype
    lvl         = TextField()      # level in which candidate is
    sig_id      = ForeignKeyField(Area_Info, db_column='sig_id', to_field='id')
    sig_id      = IntegerField()
    precinct    = TextField()      # precinct name can be unique

    # about the candidate
    name        = TextField()      # candidate name
    party       = TextField()      # party affiliation

# make tables very simple although this makes a lot of redundancies.
class Election_Info(EMDDBModel):
    # 중요! 분동된 행정동들을 산입한 경우가 있기때문에 selection이 sgg_name, emd_name에 따라 여러 row이 selection될 수 있다.
    id           = IntegerField(primary_key=True)
    # about the election
    election    = TextField()      # which election
    elec_type   = TextField()      # electiontype
    lvl         = TextField()      # level in which count is. (0: presidential) 
    sig_cd      = TextField()      # the accompanying area (foreign key to area_info)
    sig_id      = ForeignKeyField(Area_Info, db_column='sig_id', to_field='id')
    precinct    = TextField()      # precinct name can be unique
    # about the election result
    candidate_id= ForeignKeyField(Candidate_Info, db_column='candidate_id', to_field='id')
    count_type   = TextField()     # 소계 / 관외 / 관내 / 우편 / 잘못 투입
    count        = IntegerField()  # the actual count
    # 잘못투입/구분된 투표지는 count_type, 선거구(precinct level~시군구)로 보인다.

db.connect()
