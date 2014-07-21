#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gzip
import json
import os
import sys
from datetime import date, datetime, timedelta
import string
import codecs

from election_class import *

# Print all queries to stderr.
#import logging
#logger = logging.getLogger('peewee')
#logger.setLevel(logging.DEBUG)
#logger.addHandler(logging.StreamHandler())

election_data = {}

election_date = "2012-04-11"


elec = election_info.get( election_info.elec_date == election_date )

election_data[str(elec.elec_date)] = {}

print elec.elec_title

elec_area_list = elec_area_info.select().join( elec_elec_area_relation ).where( ( elec_elec_area_relation.election_info == elec.id ) )
for ea in elec_area_list:
	print ea.elec_nm
	try:
		counting = counting_info.get( ( counting_info.election_info == elec.id ) & ( counting_info.elec_area_info == ea.id ) & ( counting_info.counting_percent  == 100 ) )
	except counting_info.DoesNotExist:
		print "no such counting_info"
		continue
	try:
		result = election_result.get( ( election_result.counting_info == counting.id ) & ( election_result.elected == True ) )
	except election_result.DoesNotExist:
	 	print "no such election_result"
	
	print result.candidate_info.party_info.party_nm, result.candidate_info.person_info.name, result.vote_count, result.vote_percent

	ea_data = { 'elec_area_cd' : ea.elec_cd, 'elec_area_nm': ea.elec_nm, 
						'elect_data': { 'party_id': result.candidate_info.party_info.id, 'party_nm': result.candidate_info.party_info.party_nm,
												'person_nm': result.candidate_info.person_info.name, 'vote_count': result.vote_count, 'vote_percent': result.vote_percent }
					}
	#print ea_data
	election_data[str(elec.elec_date)][ea.elec_cd] = ea_data
	
election_data_json = "var election_data = " + json.dumps( election_data, separators = (',', ':') ) + ";"

f = codecs.open("election_data.json", encoding='utf-8', mode='w')
f.write ( election_data_json)
f.close()

#print elect_data