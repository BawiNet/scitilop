#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
#import mysql.connector
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs

from election_class import *

# Print all queries to stderr.
import logging
logger = logging.getLogger('peewee')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
print dbconfig['dbtype']

print "drop tables"
if elec_elec_area_relation.table_exists():
	elec_elec_area_relation.drop_table()
if elec_area_relation.table_exists():
	elec_area_relation.drop_table()
if election_result.table_exists():
	election_result.drop_table()
if candidate_info.table_exists():
	candidate_info.drop_table()
if counting_info.table_exists():
	counting_info.drop_table()
if elec_area_info.table_exists():
	elec_area_info.drop_table()
if area_boundary_info.table_exists():
	area_boundary_info.drop_table()
if area_info.table_exists():
	area_info.drop_table()
if election_info.table_exists():
	election_info.drop_table()
if person_info.table_exists():
	person_info.drop_table()
if party_info.table_exists():
	party_info.drop_table()

print "create tables"
area_info.create_table()
area_boundary_info.create_table()
election_info.create_table()
elec_area_info.create_table()
elec_area_relation.create_table()
elec_elec_area_relation.create_table()
person_info.create_table()
party_info.create_table()
candidate_info.create_table()
counting_info.create_table()
election_result.create_table()

