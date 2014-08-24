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
import os.path
from election_class import *
import time
import yaml
import os.path
import re

''' 선거-선거구, 선거구-행정구역 매핑 정보 입력 ''' 
def load_elec_area_data( filename ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading", filename

	json_file = open( filename, 'r' )
	elec_area_data = json.load( json_file )
	json_file.close()
		
	for elec_date in elec_area_data.keys():
		#total_count += 1
		''' 선거일 '''
		found_election = False
		try:
			e = election_info.get( election_info.elec_date == elec_date )
		except election_info.DoesNotExist:
			print "no such election", elec_date
			error_count += 1
			continue
		else:
			found_election = True
		
		elec_type_list = elec_area_data[elec_date].keys()
		elec_type_list.sort()

		for elec_type in elec_type_list:
			print elec_type
			elec_area_mapping_list = elec_area_data[elec_date][elec_type]
			for elec_area in elec_area_mapping_list:
				elec_lvl = elec_area['elec_lvl']
				try:
					ea = elec_area_info.get( ( elec_area_info.elec_cd == elec_area['elec_cd'] ) & ( elec_area_info.valid_from <= elec_date ) & ( elec_area_info.valid_to >= elec_date ) )
				except elec_area_info.DoesNotExist:
					ea = elec_area_info()
	
				ea.elec_cd = elec_area['elec_cd']
				ea.elec_nm = elec_area['elec_nm']
				if 'elect_num' in elec_area.keys():
					ea.elect_num = elec_area['elect_num']
				ea.elec_lvl = elec_area['elec_lvl']
				ea.valid_from = elec_date
				ea.valid_to = '9999-12-31'
				ea.save()
				success_count += 1
			
				try:
					eearel = elec_elec_area_relation.get( ( elec_elec_area_relation.election_info == e.id ) & ( elec_elec_area_relation.elec_area_info == ea.id ) )
				except elec_elec_area_relation.DoesNotExist:
					eearel = elec_elec_area_relation()
					eearel.election_info = e.id
					eearel.elec_area_info = ea.id
					eearel.save()
					success_count += 1
				else:
					pass
				
				if 'area_list' in elec_area.keys():
				#if elec_lvl in [ '5', '6' ]:
					area_list = elec_area['area_list']
					for area in area_list:
						total_count += 1
						sig_cd = area['sig_cd']
						sys.stdout.write('.')
						try:
							a = area_info.get_area_by_cd( sig_cd, elec_date )
							#a = area_info.get( area_info.sig_cd == sig_cd )
						except area_info.DoesNotExist:
							print "no such area", sig_cd
							error_count += 1
							continue
						if a.sig_nm != area['sig_nm']:
							print "sig_nm not matching", a.sig_nm, area['sig_nm']
							error_count += 1
							continue
						try:
							earel = elec_area_relation.get( ( elec_area_relation.area_info == a.id ) & ( elec_area_relation.elec_area_info == ea.id ) )
						except elec_area_relation.DoesNotExist:
							#print "adding", ea.elec_nm, a.sig_nm
							earel = elec_area_relation()
							earel.elec_area_info = ea.id
							earel.area_info = a.id
							earel.save()			
							success_count += 1
						else:
							#print "already there", ea.elec_nm, a.sig_nm
							pass
				else:
					if elec_lvl in [ '3', '8', '11' ]:
						nec_cd_len = 2
					elif elec_lvl in [ '4', '9' ]:
						nec_cd_len = 4
						
					nec_cd = elec_area['elec_cd'][len(elec_lvl):nec_cd_len+len(elec_lvl)]
					try:
						a = area_info.get( ( area_info.nec_cd == nec_cd ) & ( area_info.valid_from <= elec_date ) & ( area_info.valid_to >= elec_date ) )
					except area_info.DoesNotExist:
						print "no such area", elec_area['elec_nm'], "with nec_cd", nec_cd
						error_count += 1
						continue
						
					try:
						earel = elec_area_relation.get( ( elec_area_relation.area_info == a.id ) & ( elec_area_relation.elec_area_info == ea.id ) )
					except elec_area_relation.DoesNotExist:
						#print "adding", ea.elec_nm, a.sig_nm
						earel = elec_area_relation()
						earel.elec_area_info = ea.id
						earel.area_info = a.id
						earel.save()			
						success_count += 1
					else:
						#print "already there", ea.elec_nm, a.sig_nm
						pass
								
	return [ error_count, success_count, total_count ]

''' 각 선거 후보자 정보 입력 '''
def load_candidate_data( filename ):
	#print "loading", key
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0

	json_file = open( filename, 'r' )
	candidate_data_hash = json.load( json_file )
	json_file.close()

	for elec_date in candidate_data_hash.keys():
		try:
			election = election_info.get( election_info.elec_date == elec_date )
		except election_info.DoesNotExist:
			print "no election info on", elec_date
			error_count += 1
			continue
					
		elec_type_list = candidate_data_hash[elec_date].keys()
		elec_type_list.sort()
		
		for elec_type in elec_type_list:
			print elec_type
			elec_area_candidate_hash = candidate_data_hash[elec_date][elec_type]
			for elec_area_cd in elec_area_candidate_hash.keys():
				
				try:
					elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_area_cd )
				except elec_area_info.DoesNotExist:
					print "no such elec_area", elec_area_cd
					error_count += 1
					continue
				else:
					pass #print elec_area.elec_nm, elec_area.elec_cd	
				candidate_list = elec_area_candidate_hash[elec_area_cd]
				
				for candidate_data in candidate_list:
					total_count += 1
					sys.stdout.write('.')
					party_nm, cand_num, name, hanja, sex, birthdate = candidate_data
					
					try:
						party = party_info.get( ( party_info.party_nm == party_nm ) & (party_info.valid_from <= elec_date ) & ( party_info.valid_to >= elec_date ) )
					except party_info.DoesNotExist:
						#print "adding new party", party_nm 
						party = party_info()
						party.party_nm = party_nm
						party.valid_from = elec_date[:4] + "-01-01"
						party.valid_to = "9999-12-31"
						party.save()
					else:
						pass
					
					try:
						person = person_info.get( ( person_info.name == name ) & (person_info.sex == sex ) & ( person_info.birthdate == birthdate ) )
					except person_info.DoesNotExist:
						#print "adding new person", name, sex, birthdate
						person = person_info()
						person.name = name
						person.sex = sex
						person.hanja = hanja
						person.birthdate = birthdate
						person.save()
						success_count += 1
					else:
						pass_count += 1
		
					try:
						candidate = candidate_info.get(	( candidate_info.election_info == election.id ) & 
																			( candidate_info.elec_area_info == elec_area.id ) &
																			( candidate_info.party_info == party.id ) &
																			( candidate_info.person_info == person.id ) )
					except candidate_info.DoesNotExist:
						#print "adding candidate", election.elec_date, elec_area.elec_nm, party.party_nm, person.name
						candidate = candidate_info()
						candidate.election_info = election.id
						candidate.elec_area_info = elec_area.id
						candidate.party_info = party.id
						candidate.person_info = person.id
						candidate.candidate_num = cand_num
						candidate.save()
						success_count += 1
					else:
						pass_count += 1
						pass
						#print "already exist", election.elec_date, elec_area.elec_nm, party.party_nm, person.name
		

	return [ error_count, success_count, total_count ]



log_str = ""
elec_date = "2014-06-04"

filename = 'elec_area_2014-06-04.json'

print "Loading elec_area data for", elec_date, "election:"

error_count, success_count, total_count = load_elec_area_data( filename )

print "\nFinished loading elec_area data for", elec_date, "election.\nError count:", error_count, "success count:", success_count, "total_count", total_count, "\n"


filename = 'candidate_info_2014-06-04.json'

print "Loading candidate data for", elec_date, "election:"

error_count, success_count, total_count = load_candidate_data( filename )

print "\nFinished loading candidate data for", elec_date, "election.\nError count:", error_count, "success count:", success_count, "total_count", total_count, "\n"

