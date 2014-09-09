#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
from datetime import date, datetime, timedelta
from peewee import *
import string

from election_class import *

import yaml
import os.path

import argparse
from argparse import RawTextHelpFormatter

''' 선거-선거구, 선거구-행정구역 매핑 정보 입력 ''' 
def load_elec_area_info( key, config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading", filename

	info_type = config['elec_area_info']['type']
	if info_type == 'file':
		filename = config['elec_area_info']['location']
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
def load_candidate_info( key, config):
	#print "loading", key
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0

	info_type = config['candidate_info']['type']
	if info_type == 'file':
		filename = config['candidate_info']['location']
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

					if party_nm != "":
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
						party_id = party.id
					else:
						party_id = None

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
																			( candidate_info.party_info == party_id ) &
																			( candidate_info.person_info == person.id ) )
					except candidate_info.DoesNotExist:
						#print "adding candidate", election.elec_date, elec_area.elec_nm, party.party_nm, person.name
						candidate = candidate_info()
						candidate.election_info = election.id
						candidate.elec_area_info = elec_area.id
						candidate.party_info = party_id
						candidate.person_info = person.id
						candidate.candidate_num = cand_num
						candidate.save()
						success_count += 1
					else:
						pass_count += 1
						pass
						#print "already exist", election.elec_date, elec_area.elec_nm, party.party_nm, person.name
		

	return [ error_count, success_count, total_count ]

''' 선거 결과 입력 '''
def load_election_result( key, config ):
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0
	#print "loading", key
	info_type = config[key]['type']
	if info_type == 'file':
		filename = config[key]['location']
		#print filename
		json_file = open( filename, 'r' )
		json_data = json_file.read()
		result_data_hash = json.loads( json_data )
		json_file.close()

		for elec_date in result_data_hash.keys():
			try:
				elec = election_info.get( election_info.elec_date == elec_date )
			except election_info.DoesNotExist:
				print "no such election!"
				continue
			
			elec_type_list = result_data_hash[elec_date].keys()
			elec_type_list.sort()

			for elec_type in elec_type_list:
				print elec_type
				#print elec.elec_title, elec.elec_date
				for elec_area_cd in result_data_hash[elec_date][elec_type].keys():
					try:
						elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_area_cd )
					except elec_area_info.DoesNotExist:
						print "no such elec_area!"
						continue
					#print elec_area.elec_nm

					vote_result = result_data_hash[elec_date][elec_type][elec_area_cd]['vote_result']
					try:
						counting = counting_info.get( ( counting_info.election_info == elec.id ) &
																		( counting_info.elec_area_info == elec_area.id ) &
																		( counting_info.counting_percent == 100.0 ) )
					except counting_info.DoesNotExist:
						#print "counting_info add", elec.elec_title, elec_area.elec_nm, vote_result[1], "/", vote_result[0]
						counting = counting_info()
						counting.election_info = elec.id
						counting.elec_area_info = elec_area.id
						counting.counting_percent = 100.0
						counting.eligible_count = vote_result[0]
						counting.vote_count = vote_result[1]
						counting.invalid_count = vote_result[2]
						counting.abstention_count = vote_result[3]

						counting.save()
						#print counting.election_info.elec_title, counting.elec_area_info.elec_nm, counting.counting_percent

					max_vote = 0
					max_vote_result_id = -1
					vote_result_list = result_data_hash[elec_date][elec_type][elec_area_cd]['candidate_result']

					candidate_list = [ c for c in candidate_info.select().where( ( candidate_info.election_info == elec.id ) &
																												( candidate_info.elec_area_info == elec_area.id ) ) ]
					eresult_list = []
					# 정당 및 후보자 정보 없으면 오류.
					for vote_result in vote_result_list:
						total_count += 1
						sys.stdout.write('.')
						candidate_num, party_nm, candidate_nm, sex, vote_count, vote_percent = vote_result
						#print "  ",party_nm, candidate_nm

						if candidate_nm != '':

							candidate = candidate_info()
							candidate_found = False
							# 후보자 정보 찾기
							for c in candidate_list:
								#print c.party_info.party_nm, party_nm, c.person_info.name, candidate_nm #, c.candidate_num, type( c.candidate_num ), candidate_num, type( candidate_num )
								if c.person_info.name == candidate_nm and ( c.party_info == None or ( c.party_info != None and c.party_info.party_nm == party_nm ) ):# and c.candidate_num == candidate_num:
									# 찾았음
									candidate = c
									candidate_found = True
									break
							if candidate_found == False:
								error_count += 1
								print "cannot find candidate", elec.elec_date, elec_area.elec_nm, candidate_num, party_nm, candidate_nm, sex
								continue
							party_id = None
							candidate_id = candidate.id
						else: #비례대표일 경우
							try:
								party = party_info.get( (party_info.party_nm == party_nm) & ( party_info.valid_from <= elec_date ) & ( party_info.valid_to >= elec_date ))
							except party_info.DoesNotExist:
								print "cannot find party", elec.elec_date, elec_area.elec_nm, candidate_num, party_nm
							party_id = party.id
							candidate_id = None
						try:
							eresult = election_result.get( ( election_result.counting_info == counting.id ) & (election_result.candidate_info == candidate_id ) & (election_result.party_info == party_id )  )
						except election_result.DoesNotExist:
							#print "adding result", elec.elec_title, elec_area.elec_nm, candidate.person_info.name, vote_count, vote_percent
							eresult = election_result()
							eresult.counting_info = counting.id
							eresult.candidate_info = candidate_id
							eresult.party_info = party_id
							eresult.vote_count = vote_count
							eresult.vote_percent = vote_percent
							eresult.save()
							success_count += 1
						eresult_list.append( eresult )
					#for r in eresult_list:
					#	print r.vote_count
					eresult_list.sort( key=lambda x:x.vote_count, reverse = True)
					#for r in eresult_list:
					#	print r.vote_count
					if elec_type in [ '8', '9' ]:

						pass
					else:
						for i in range( elec_area.elect_num ):
							eresult = eresult_list[i]
							candidate = eresult.candidate_info
							candidate.elected = True
							candidate.save()



	return [ error_count, success_count, total_count ]

def load_elected_data( key, config ):
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0
	#print "loading", key
	info_type = config[key]['type']
	if info_type == 'file':
		filename = config[key]['location']
		#print filename
		json_file = open( filename, 'r' )
		json_data = json_file.read()
		elected_data_hash = json.loads( json_data )
		json_file.close()

		for elec_date in elected_data_hash.keys():
			try:
				elec = election_info.get( election_info.elec_date == elec_date )
			except election_info.DoesNotExist:
				print "no such election!"
				continue

			elec_type_list = elected_data_hash[elec_date].keys()
			elec_type_list.sort()

			for elec_type in elec_type_list:
				print elec_type
				#print elec.elec_title, elec.elec_date
				for elec_area_cd in elected_data_hash[elec_date][elec_type].keys():

					try:
						elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_area_cd )

					except elec_area_info.DoesNotExist:
						print "no such elec_area!"
						continue
					#print elec_area.elec_nm

					elected_list = elected_data_hash[elec_date][elec_type][elec_area_cd]['elected_list']
					candidate_list = elec_area.candidates

					for elected in elected_list:
						total_count += 1
						found = False
						for candidate in candidate_list:
							#print candidate.person_info.name, elected['name'], candidate.person_info.birthdate, elected['birthdate']
							if candidate.person_info.name == elected['name'] and str(candidate.person_info.birthdate) == elected['birthdate']:
								found = True
								success_count += 1
								candidate.elected = True
								candidate.save()
						if found == False:
							error_count += 1
							print "cannot find candidate", elec_area.elec_cd, elec_area.elec_cd, elected['name'], elected['birthdate']

	return [ error_count, success_count, total_count ]

''' 선거 상세 결과 입력 '''
def load_election_result_detail( key, config ):
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0
	#print "loading", key
	info_type = config[key]['type']
	if info_type == 'file':
		filename = config[key]['location']
		#print filename
		json_file = open( filename, 'r' )
		json_data = json_file.read()
		result_data_hash = json.loads( json_data )
		json_file.close()

		for elec_date in result_data_hash.keys():
			try:
				elec = election_info.get( election_info.elec_date == elec_date )
			except election_info.DoesNotExist:
				print "no such election!"
				continue
			pass
	return [ error_count, success_count, total_count ]

prog_desc = u'선거정보 입력도구'
parser = argparse.ArgumentParser(description=prog_desc, formatter_class=RawTextHelpFormatter)

parser.add_argument('config_file', help=u'선거정보 관련 파일들의 위치가 담긴 YAML 파일.')

args = parser.parse_args()
print args.config_file

config_filename = args.config_file

if os.path.isfile( config_filename  ):
	f = open( config_filename, 'r')
	election_data_config = yaml.load(f)
	f.close()

key_list = [ 'elec_area_info', 'candidate_info', 'election_result', 'elected_data', 'election_result_detail' ]

for key in key_list:
	if key not in election_data_config.keys():
		continue
	print "Loading", key
	error_count = 0
	success_count = 0
	total_count = 0
	if key == 'elec_area_info':
		error_count, success_count, total_count = load_elec_area_info( key, election_data_config )
	elif key == 'candidate_info':
		error_count, success_count, total_count = load_candidate_info( key, election_data_config )
	elif key == 'election_result':
		error_count, success_count, total_count = load_election_result( key, election_data_config )
	elif key == 'elected_data':
		error_count, success_count, total_count = load_elected_data( key, election_data_config )
	elif key == 'election_result_detail':
		error_count, success_count, total_count = load_election_result_detail( key, election_data_config )
	print "\nFinished loading", key, "data.\nError count:", error_count, "success count:", success_count, "total_count", total_count, "\n"
