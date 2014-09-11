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

from election_class import *

import yaml
import os.path

eligible_count_hash = {}

ci_list1 = counting_info.select( counting_info, fn.Sum(counting_info.eligible_count).alias('count') ).where( ( counting_info.station_id == None ) & ( counting_info.election_info == 1 )).group_by( counting_info.elec_area_info )
ci_list2 = counting_info.select( counting_info, fn.Sum(counting_info.eligible_count).alias('count') ).where( ( counting_info.station_id != None ) & ( counting_info.election_info == 1 )).group_by( counting_info.elec_area_info )
for ci in ci_list1:
    #print ci.elec_area_info.elec_cd, ci.count
    eligible_count_hash[ci.elec_area_info.elec_cd] = { 'null_count': ci.count, 'elec_nm': ci.elec_area_info.elec_nm }

for ci in ci_list2:
    #print ci.elec_area_info.elec_cd, ci.count
    eligible_count_hash[ci.elec_area_info.elec_cd]['not_null_count'] = ci.count


log_str = ""
#print eligible_count_hash

for k in eligible_count_hash.keys():
    if eligible_count_hash[k]['null_count'] != eligible_count_hash[k]['not_null_count']:
        print k, eligible_count_hash[k]['elec_nm'], "null count", eligible_count_hash[k]['null_count'], "not null count", eligible_count_hash[k]['not_null_count']