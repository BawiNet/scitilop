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
basedata_config = {}
basedata_config_filename = "./basedataconfig.yaml"

if os.path.isfile( basedata_config_filename  ):
	f = open( basedata_config_filename, 'r')
	basedata_config = yaml.load(f)
	f.close()

#print basedata_config

''' 선거정보 입력 '''
if 'election_info' in basedata_config.keys():
	print "loading election_info"
	info_type = basedata_config['election_info']['type']
	if info_type == 'file':
		filename = basedata_config['election_info']['location']
		json_file = open( filename, 'r' )
		election_info_list = json.load( json_file )
		json_file.close()
		for elec_data in election_info_list:
			try:
				elec = election_info.get( election_info.elec_date == elec_data[2] )
				
			except election_info.DoesNotExist:
				print "new election data", elec_data[2]
				elec = election_info()
				elec.elec_lvl, elec.elec_title, elec.elec_date = elec_data
				elec.save()
				continue
			
			print "already exist", elec_data[2]

''' 선거구정보 입력 '''
key = 'elec_area_info'
if key in basedata_config.keys():
	print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		elec_area_list = json.load( json_file )
		json_file.close()
		for elec_data in elec_area_list:
			elec_cd, elec_lvl, elec_nm, parent_cd = elec_data
			#elec_data = elec_area_hash[elec_cd]
			try:
				ea = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
				
			except elec_area_info.DoesNotExist:
				print "new elec_area data", elec_cd, elec_data
				ea = elec_area_info()
				ea.elec_cd = elec_cd
				ea.elec_lvl = elec_lvl
				ea.elec_nm = elec_nm
				ea.valid_from = "2012-01-01"
				ea.valid_to = "9999-12-31"
				if parent_cd != "":
					try:
						p_ea = elec_area_info.get( elec_area_info.elec_cd == parent_cd )
					except:
						print "no such parent data"
					ea.parent_elec = p_ea.id
				ea.save()
				continue
			else:
				print "already exist", elec_cd, elec_data


''' 행정구역 정보 입력 ''' 
if 'area_info' in basedata_config.keys():
	print "loading area_info"
	info_type = basedata_config['area_info']['type']
	if info_type == 'dir':
		location = basedata_config['area_info']['location']
		print location
		for dirname, dirnames, filenames in os.walk( location ):
			for filename in filenames:
				elems = filename.split( "." )
				sig_lvl = int( elems[3] )
				lvl1_cd = elems[2]
				fullpath = os.path.join(dirname, filename)	
				print fullpath
				if( fullpath.endswith('gz') ):
				    json_data = gzip.open(fullpath,'rb')
				else:
					json_data = open(fullpath,'r')
				actual_data = json.load( json_data )
				json_data.close()
		
				for data in actual_data['features']:
					try:
						area = area_info.get( area_info.sig_cd == data['properties']['Name'] )
						print "already exist", data['properties']['Name'], data['properties']['Description']
					except area_info.DoesNotExist:
						print "new data", data['properties']['Name'], data['properties']['Description'], sig_lvl
						area = area_info()
						area.sig_cd = data['properties']['Name']
						area.sig_nm = data['properties']['Description']
						area.geoJSON = json.dumps( data['geometry'], ensure_ascii = False, separators=(',', ': ') ) 
						area.valid_from = "1948-08-15"
						area.valid_to = "9999-12-31"
						area.coord_sys = "WGS84"
						area.sig_lvl = str( sig_lvl	)
						area.check_parent()
						area.save()


''' 선거-선거구 매핑 정보 입력: deprecated '''  

key = 'elec_elec_area_relation'
if False:
#if key in basedata_config.keys():
	print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		eea_relation_hash = json.load( json_file )
		json_file.close()
		for elec_date in eea_relation_hash.keys():
			elec_cd_list = eea_relation_hash[elec_date]
			try:
				elec = election_info.get( election_info.elec_date == elec_date )
			except election_info.DoesNotExist:
				print "no such election", elec_date
			else:
				for elec_cd in elec_cd_list:
					try:
						elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
					except elec_area_info.DoesNotExist:
						print "no such elec_area", elec_cd
					else:	
						try:
							eearel = elec_elec_area_relation.get( ( elec_elec_area_relation.election_info == elec.id ) & ( elec_elec_area_relation.elec_area_info == elec_area.id ) )
						except elec_elec_area_relation.DoesNotExist:
							print "adding elec_elec_area_relation", elec_date, elec_cd
							eearel = elec_elec_area_relation()
							eearel.election_info = elec.id
							eearel.elec_area_info = elec_area.id
							eearel.save()
						else:
							print "already exist", elec_date, elec_cd, eearel.id


''' 선거-선거구, 선거구-행정구역 매핑 정보 입력 ''' 

key = 'elec_area_relation'
if key in basedata_config.keys():
	print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		ea_master_relation_hash = json.load( json_file )
		json_file.close()
		
		for elec_date in ea_master_relation_hash.keys():
			''' 선거일 '''
			found_election = False
			try:
				e = election_info.get( election_info.elec_date == elec_date )
			except election_info.DoesNotExist:
				print "no such election", elec_date
			else:
				found_election = True
			elec_area_mapping_hash = ea_master_relation_hash[elec_date]
		
			for elec_cd in elec_area_mapping_hash .keys():
			
				try:
					ea = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
				except elec_area_info.DoesNotExist:
					print "no such elec_area", elec_cd
					continue
				if( ea.elec_nm != elec_area_mapping_hash[elec_cd]['elec_nm'] ):
					print "elec_nm not matching", ea.elec_nm, elec_area_mapping_hash['elec_nm']
					continue
			
				if found_election:
					try:
						eearel = elec_elec_area_relation.get( ( elec_elec_area_relation.election_info == e.id ) & ( elec_elec_area_relation.elec_area_info == ea.id ) )
					except elec_elec_area_relation.DoesNotExist:
						print "adding", e.elec_title, ea.elec_nm
						eearel = elec_elec_area_relation()
						eearel.election_info = e.id
						eearel.elec_area_info = ea.id
						eearel.save()
					else:
						print "already exist", e.elec_title, ea.elec_nm
			
			
				area_hash = elec_area_mapping_hash[elec_cd]['area_hash']
				for sig_cd in area_hash.keys():
					try:
						a = area_info.get( area_info.sig_cd == sig_cd )
					except area_info.DoesNotExist:
						print "no such area", sig_cd
						continue
					if a.sig_nm != area_hash[sig_cd]:
						print "sig_nm not matching", a.sig_nm, area_hash[sig_cd]
						continue
					try:
						earel = elec_area_relation.get( ( elec_area_relation.area_info == a.id ) & ( elec_area_relation.elec_area_info == ea.id ) )
					except elec_area_relation.DoesNotExist:
						print "adding", ea.elec_nm, a.sig_nm
						earel = elec_area_relation()
						earel.elec_area_info = ea.id
						earel.area_info = a.id
						earel.save()			
					else:
						print "already there", ea.elec_nm, a.sig_nm

''' 정당정보 입력 '''
key = 'party_info'
if key in basedata_config.keys():
	print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		party_data_hash = json.load( json_file )
		json_file.close()
		for party_rep_nm in party_data_hash.keys():
			party_info_list = party_data_hash[party_rep_nm]
			party_list = []
			for party_data in party_info_list:
				party_nm, valid_from, valid_to = party_data
				try:
					party = party_info.get( ( party_info.party_nm == party_nm ) & ( party_info.valid_from == valid_from ) )
				except party_info.DoesNotExist:
					print "new party data", party_nm, valid_from, valid_to
					party = party_info()
					party.party_nm = party_nm
					party.valid_from = valid_from
					party.valid_to = valid_to
					if len( party_list ) > 0 :
						party.next_party = party_list[-1].id
					party.save()
					if len( party_list ) > 0 :
						party_list[-1].prev_party = party.id
						party_list[-1].save()
					party_list.append( party )
				else:
					print "already exist", party_nm, valid_from


''' 각 선거 후보자 정보 입력 '''
key = 'candidate_info'
if key in basedata_config.keys():
	print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		candidate_data_hash = json.load( json_file )
		json_file.close()
		for elec_date in candidate_data_hash.keys():
			try:
				election = election_info.get( election_info.elec_date == elec_date )
			except election_info.DoesNotExist:
				print "no election info on", elec_date
				continue
						
			elec_area_candidate_hash = candidate_data_hash[elec_date]
			for elec_area_cd in elec_area_candidate_hash.keys():
				
				try:
					elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_area_cd )
				except elec_area_info.DoesNotExist:
					print "no such elec_area", elec_area_cd
					continue
				else:
					print elec_area.elec_nm, elec_area.elec_cd	
				candidate_list = elec_area_candidate_hash[elec_area_cd]
				
				for candidate_data in candidate_list:
					party_nm, cand_num, name, hanja, sex, birthdate = candidate_data
					
					try:
						party = party_info.get( ( party_info.party_nm == party_nm ) & (party_info.valid_from < elec_date ) & ( party_info.valid_to > elec_date ) )
					except party_info.DoesNotExist:
						print "adding new party", party_nm 
						party = party_info()
						party.party_nm = party_nm
						party.valid_from = elec_date[:4] + "-01-01"
						party.valid_to = "9999-12-31"
						party.save()
					
					try:
						person = person_info.get( ( person_info.name == name ) & (person_info.sex == sex ) & ( person_info.birthdate == birthdate ) )
					except person_info.DoesNotExist:
						print "adding new person", name, sex, birthdate
						person = person_info()
						person.name = name
						person.sex = sex
						person.hanja = hanja
						person.birthdate = birthdate
						person.save()

					try:					
						candidate = candidate_info.get(	( candidate_info.election_info == election.id ) & 
																			( candidate_info.elec_area_info == elec_area.id ) &
																			( candidate_info.party_info == party.id ) &
																			( candidate_info.person_info == person.id ) )
					except candidate_info.DoesNotExist:
						print "adding candidate", election.elec_date, elec_area.elec_nm, party.party_nm, person.name
						candidate = candidate_info()
						candidate.election_info = election.id
						candidate.elec_area_info = elec_area.id
						candidate.party_info = party.id
						candidate.person_info = person.id
						candidate.candidate_num = cand_num
						candidate.save()
					else:
						print "already exist", election.elec_date, elec_area.elec_nm, party.party_nm, person.name
		

''' 역대 선거 결과 입력 '''
key = 'election_result'
if key in basedata_config.keys():
	print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		print filename
		json_file = open( filename, 'r' )
		json_data = json_file.read()
		#print json_data
		result_data_hash = json.loads( json_data )
		#result_data_hash = json.load( json_file)
		json_file.close()


		for elec_date in result_data_hash.keys():
			try:
				elec = election_info.get( election_info.elec_date == elec_date )
			except election_info.DoesNotExist:
				print "no such election!"
				continue
			
			print elec.elec_title, elec.elec_date
			for elec_area_cd in result_data_hash[elec_date].keys():
				try:
					elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_area_cd )
				except elec_area_info.DoesNotExist:
					print "no such elec_area!"
					continue
				print elec_area.elec_nm
		
				vote_result = result_data_hash[elec_date][elec_area_cd]['vote_result']
				try:
					counting = counting_info.get( ( counting_info.election_info == elec.id ) &
																	( counting_info.elec_area_info == elec_area.id ) &
																	( counting_info.counting_percent == 100.0 ) )
				except counting_info.DoesNotExist:
					print "counting_info add", elec.elec_title, elec_area.elec_nm, vote_result[1], "/", vote_result[0]
					counting = counting_info()
					counting.election_info = elec.id
					counting.elec_area_info = elec_area.id
					counting.counting_percent = 100.0
					counting.eligible_count = vote_result[0]
					counting.vote_count = vote_result[1]
					counting.invalid_count = vote_result[2]
					counting.abstention_count = vote_result[3]
					
					counting.save()
					print counting.election_info.elec_title, counting.elec_area_info.elec_nm, counting.counting_percent
		
				max_vote = 0
				max_vote_result_id = -1
				vote_result_list = result_data_hash[elec_date][elec_area_cd]['candidate_result']
		
				candidate_list = [ c for c in candidate_info.select().where( ( candidate_info.election_info == elec.id ) &
																											( candidate_info.elec_area_info == elec_area.id ) ) ]
		
				# 정당 및 후보자 정보 없으면 오류.
				for vote_result in vote_result_list:
					candidate_num, party_nm, candidate_nm, sex, vote_count, vote_percent = vote_result
					print "  ",party_nm, candidate_nm
					
					candidate = candidate_info()
					candidate_found = False
					# 후보자 정보 찾기
					for c in candidate_list:
						#print c.party_info.party_nm, party_nm, c.person_info.name, candidate_nm #, c.candidate_num, type( c.candidate_num ), candidate_num, type( candidate_num )
						if c.party_info.party_nm == party_nm and c.person_info.name == candidate_nm:# and c.candidate_num == candidate_num:
							# 찾았음
							candidate = c
							candidate_found = True
							break
					if candidate_found == False:
						print "cannot find candidate", elec.elec_date, ea.elec_nm, candidate_num, party_nm, candidate_nm, sex
						continue

					''' obsolete 8.1.2014 동명이인이 있을 경우 인물정보 잘못 가져오는 경우 있음. 후보자 정보가 이미 있다고 가정하고 짜는 편이 나음.
					try:
						party = party_info.get( ( party_info.party_nm == party_nm ) & ( party_info.valid_from < elec_date  ) & ( party_info.valid_to > elec_date ) )
					except party_info.DoesNotExist:
						print "adding party", party_nm, elec_date
						party = party_info()
						party.party_nm = party_nm
						party.valid_from = elec_date[:4] + "-01-01"
						party.valid_to = "9999-12-31"
						party.save()
					else:
						print "already exist", party_nm
		
					try:
						person = person_info.get( ( person_info.name == candidate_nm ) & ( person_info.sex == sex ) ) # 후보자 정보 동명이인 확인할 것.
					except person_info.DoesNotExist:
						print "adding person", candidate_nm
						person = person_info()
						person.name = candidate_nm
						person.sex = sex
						person.birthdate = None
						person.save()
					
					#print "find:", elec.elec_title, elec_area.elec_nm, party.party_nm, person.id, person.name
					try:
						print "find candidate", elec.id,elec_area.id, party.id, person.id, person.name
						candidate = candidate_info.get( ( candidate_info.election_info == elec.id ) &
																			( candidate_info.elec_area_info == elec_area.id ) &
																			( candidate_info.person_info == person.id ) &
																			( candidate_info.party_info == party.id ) )
					except candidate_info.DoesNotExist:
						print "adding candidate", elec.id,elec.elec_title,elec_area.elec_nm, party.party_nm, person.name
						candidate = candidate_info()
						candidate.election_info = elec.id
						candidate.elec_area_info = elec_area.id
						candidate.party_info = party.id
						candidate.person_info = person.id
						candidate.candidate_num = candidate_num
						candidate.save()
						
					else:
						
						print "already_exist:", candidate.election_info.elec_title, candidate.elec_area_info.elec_nm, candidate.party_info.party_nm, candidate.person_info.id, candidate.person_info.name
					'''
					
					try:
						eresult = election_result.get( ( election_result.counting_info == counting.id ) & (election_result.candidate_info == candidate.id ) )
					except election_result.DoesNotExist:
						print "adding result", elec.elec_title, elec_area.elec_nm, candidate.person_info.name, vote_count, vote_percent
						eresult = election_result()
						eresult.counting_info = counting.id
						eresult.candidate_info = candidate.id
						eresult.vote_count = vote_count
						eresult.vote_percent = vote_percent
						eresult.save()

						if max_vote < vote_count:
							max_vote = vote_count
							max_vote_result_id = eresult.id
				
				if max_vote_result_id > 0:
					eresult = election_result.get( election_result.id == max_vote_result_id )
					eresult.elected = True
					eresult.save()
