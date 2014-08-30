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
from libgeojson import *

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
def load_election_info( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading election_info"
	info_type = basedata_config['election_info']['type']
	if info_type == 'file':
		filename = basedata_config['election_info']['location']
		json_file = open( filename, 'r' )
		election_info_list = json.load( json_file )
		json_file.close()
		for elec_data in election_info_list:
			total_count += 1
			sys.stdout.write('.')
			try:
				elec = election_info.get( election_info.elec_date == elec_data[2] )
				
			except election_info.DoesNotExist:
				#print "new election data", elec_data[2]
				elec = election_info()
				elec.elec_lvl, elec.elec_title, elec.elec_date = elec_data
				elec.save()
				success_count += 1

	return [ error_count, success_count, total_count ]

''' 선거구정보 입력 '''
def load_elec_area_info( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		elec_area_hash = json.load( json_file )
		json_file.close()
		for elec_date in elec_area_hash.keys():
			elec_area_list = elec_area_hash[elec_date]
			for elec_data in elec_area_list:
				total_count += 1
				sys.stdout.write('.')
				elec_cd, elec_lvl, elec_nm, parent_cd = elec_data
				#elec_data = elec_area_hash[elec_cd]
				try:
					ea = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
					
				except elec_area_info.DoesNotExist:
					#print "new elec_area data", elec_cd, elec_data
					ea = elec_area_info()
					ea.elec_cd = elec_cd
					ea.elec_lvl = elec_lvl
					ea.elec_nm = elec_nm
					ea.valid_from = elec_date
					ea.valid_to = "9999-12-31"
					if parent_cd != "":
						try:
							p_ea = elec_area_info.get( elec_area_info.elec_cd == parent_cd )
						except:
							pass
							#print "no such parent data"
						ea.parent_elec = p_ea.id
					ea.save()
					success_count += 1
				else:
					pass
					#print "already exist", elec_cd, elec_data
	return [ error_count, success_count, total_count ]


''' 행정구역 정보 입력 2014 년 기준'''
def load_area_info( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading area_info"
	info_type = basedata_config['area_info']['type']
	if info_type == 'dir':
		location = basedata_config['area_info']['location']
		#print location
		for dirname, dirnames, filenames in os.walk( location ):
			filenames.sort()
			for filename in filenames:
				sys.stdout.write('.')
				elems = filename.split( "." )
				sig_lvl = int( elems[3] )
				lvl1_cd = elems[2]
				fullpath = os.path.join(dirname, filename)	
				#print fullpath
				if( fullpath.endswith('gz') ):
				    json_data = gzip.open(fullpath,'rb')
				else:
					json_data = open(fullpath,'r')
				actual_data = json.load( json_data )
				json_data.close()
		
				for data in actual_data['features']:
					total_count += 1
					#sys.stdout.write('.')
					try:
						area = area_info.get( area_info.sig_cd == data['properties']['Name'] )
						#print "already exist", data['properties']['Name'], data['properties']['Description']
					except area_info.DoesNotExist:
						#print "new data", data['properties']['Name'], data['properties']['Description'], sig_lvl
						area = area_info()
						area.sig_cd = data['properties']['Name']
						area.sig_nm = data['properties']['Description']
						area.valid_from = "1948-08-15"
						area.valid_to = "9999-12-31"
						area.coord_sys = "WGS84"
						area.sig_lvl = str( sig_lvl	)
						area.check_parent()
						area.save()
						boundary= area_boundary_info()
						boundary.valid_from = "1948-08-15"
						boundary.valid_to = "9999-12-31"
						boundary.geojson= json.dumps( data['geometry'], ensure_ascii = False, separators=(',', ': ') ) 
						boundary.area_info = area.id
						boundary.save()
						success_count += 1
	return [ error_count, success_count, total_count ]

def load_area_info_history( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading area_info_history"
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		area_info_history_hash = json.load( json_file )
		json_file.close()

		for change_date in area_info_history_hash.keys():
			changes_list = area_info_history_hash[change_date]
			#print change_date
			for change in changes_list:
				total_count += 1
				#print change['sig_cd']
				sys.stdout.write('.')
				new_cd = change['sig_cd']
				if change['type'] == u'신설':
					try:
						area = area_info.get_area_by_cd( new_cd, change_date )
					except area_info.DoesNotExist:
						#print "adding new area_info", new_cd, change['sig_nm']
						area = area_info()
						area.sig_cd = new_cd
						area.sig_nm = change['sig_nm']
						area.valid_to = "9999-12-31"
						if 'spcity_cd' in change.keys(): # 특정시 처리
							area.spcity_cd = change['spcity_cd']
							if change['spcity_cd'] == '1':
								#print new_cd, new_cd[:4]
								#area_info.update( spcity_cd = '2' ).where( area_info.sig_cd.startswith( new_cd[:4] ) )
								suba_select = area_info.select().where( ( area_info.sig_cd.startswith( new_cd[:4] ) ) & ( area_info.sig_lvl == '2' ) )
								suba_list = [ suba for suba in suba_select ]
								for suba in suba_list:
									#print "suba", suba.sig_nm
									suba.spcity_cd = '2'
									suba.save()
					else:
						pass
						#print "updating area_info that already exists", new_cd, change['sig_nm']
						#continue
					area.valid_from = change_date
					area.check_sig_lvl()
					parent = area.check_parent()
					if parent == None:
						print "no parent for", area.sig_cd
						error_count += 1
						continue
					area.save()
					area.check_boundary()
					success_count += 1
				elif change['type'] == u'변경': # 코드/행정구역명이 바뀌는 경우. 경계는 안 바뀜.
					try:
						area = area_info.get_area_by_cd( new_cd, change_date )
						#print "updating area_info", new_cd, change['sig_nm']
					except area_info.DoesNotExist:
						#print "adding new area_info", new_cd, change['sig_nm']
						area = area_info()
						area.sig_cd = new_cd
						area.sig_nm = change['sig_nm']
						area.valid_to = "9999-12-31"
					area.valid_from = change_date
					sig_lvl = area.check_sig_lvl()
					parent = area.check_parent()
					if parent == None:
						print "no parent for", area.sig_cd
						error_count += 1
						continue
					area.save()
		
					try:
						last_date = calculate_date( change_date, -1 )
						prev_area = area_info.get_area_by_cd( change['prev_area'][0]['sig_cd'], last_date )
						#prev_area = area_info.get( area_info.sig_cd == change['prev_cd'] )
						#print "updating area_info", change['prev_area'][0]['sig_cd'], change['prev_area'][0]['sig_nm']
					except area_info.DoesNotExist:
						#print "adding new area_info", change['prev_area'][0]['sig_cd'], change['prev_area'][0]['sig_nm']
						prev_area = area_info()
						prev_area.sig_cd = change['prev_area'][0]['sig_cd']
						prev_area.sig_nm = change['prev_area'][0]['sig_nm']
						prev_area.valid_from = "1948-08-15"

					prev_area.valid_to = calculate_date( change_date, -1 )
					prev_area.next_area = area.id
					sig_lvl = prev_area.check_sig_lvl()
					parent = prev_area.check_parent()
					if parent == None:
						error_count += 1
						print "no parent for", prev_area.sig_cd
						continue
					prev_area.save()
					prev_area.check_boundary()
		
					area.prev_area = prev_area.id
					area.save()
					area.check_boundary()
					area.fill_boundary( prev_area )
					success_count += 1

				elif change['type'] == u'경계변경':
					#print u"경계변경"
					try:
						area = area_info.get_area_by_cd( change['sig_cd'], change_date )
					except area_info.DoesNotExist:
						error_count += 1
						print "no such area", change['sig_cd'], change_date
						continue
					
					area.expire_boundary( change_date )
					success_count += 1
				elif change['type'] == u'분리':
					#print u"분리"
					try:
						#prev_area = area_info.get( area_info.sig_cd == change['prev_cd'] )
						prev_area = area_info.get_area_by_cd( change['sig_cd'], change_date )
					except area_info.DoesNotExist:
						prev_area = area_info()
						prev_area.sig_cd = change['sig_cd']
						prev_area.sig_nm = change['sig_nm']
						prev_area.valid_from = "1948-08-15"
					prev_area.valid_to = calculate_date( change_date, -1 )
					sig_lvl = prev_area.check_sig_lvl()
					parent = prev_area.check_parent()
					if parent == None:
						error_count += 1
						print "no parent for", prev_area.sig_cd
						continue
					prev_area.next_area = None
					prev_area.save()
					prev_area.check_boundary()

					for next_data in change['next_area']:		
						try:
							area = area_info.get_area_by_cd( next_data['sig_cd'], change_date )
							#area = area_info.get( area_info.sig_cd == new_cd )
						except area_info.DoesNotExist:
							area = area_info()
							area.sig_cd = next_data['sig_cd']
							area.sig_nm = next_data['sig_nm']
							area.valid_to = "9999-12-31"
						area.valid_from = change_date
						sig_lvl = area.check_sig_lvl()
						parent = area.check_parent()
						if parent == None:
							error_count += 1
							print "no parent for", area.sig_cd
							continue
						area.prev_area = prev_area.id
						area.save()
						area.check_boundary()
					success_count += 1
				elif change['type'] == u'통합':
					#print u"통합"
					try:
						#area = area_info.get( area_info.sig_cd == new_cd )
						area = area_info.get_area_by_cd( new_cd, change_date )
					except area_info.DoesNotExist:
						area = area_info()
						area.sig_cd = new_cd
						area.sig_nm = change['sig_nm']
						area.valid_to = "9999-12-31"
					area.valid_from = change_date
					sig_lvl = area.check_sig_lvl()
					parent = area.check_parent()
					if parent == None:
						error_count += 1
						print "no parent for", area.sig_cd
						continue
					area.prev_area = None
					area.save()
					area.check_boundary()

					#geojson_list = []
					for prev_data in change['prev_area']:		
						try:
							#prev_area = area_info.get( area_info.sig_cd == change['prev_cd'] )
							prev_area = area_info.get_area_by_cd( prev_data['sig_cd'], change_date )
						except area_info.DoesNotExist:
							prev_area = area_info()
							prev_area.sig_cd = prev_data['sig_cd']
							prev_area.sig_nm = prev_data['sig_nm']
							prev_area.valid_from = "1948-08-15"
						prev_area.valid_to = calculate_date( change_date, -1 )
						sig_lvl = prev_area.check_sig_lvl()
						parent = prev_area.check_parent()
						if parent == None:
							error_count += 1
							print "no parent for", prev_area.sig_cd
							continue
						prev_area.next_area = area.id
						prev_area.save()
						prev_area.check_boundary()
					success_count += 1
				elif change['type'] == u'폐지':
					#print u"폐지"
					try:
						#area = area_info.get( area_info.sig_cd == new_cd )
						area = area_info.get_area_by_cd( new_cd, change_date )
					except area_info.DoesNotExist:
						area = area_info()
						area.sig_cd = new_cd
						area.sig_nm = change['sig_nm']
						area.valid_from = "1948-08-15"
					area.valid_to = calculate_date( change_date, -1 )
					sig_lvl = area.check_sig_lvl()
					parent = area.check_parent()
					if parent == None:
						error_count += 1
						print "no parent for", area.sig_cd
						continue
					area.save()
					area.check_boundary()
					success_count += 1
	return [ error_count, success_count, total_count ]

''' 비어 있는 geojson 채우기 '''
def load_missing_geojson( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	boundary_list = [ boundary for boundary in area_boundary_info.select().where( area_boundary_info.geojson == None ) ]
	for boundary in boundary_list:
		total_count += 1
		sys.stdout.write('.')
		area = boundary.area_info
		sig_cd = area.sig_cd
		year = boundary.valid_to.year
		#year = int( y )
		if year < 9999:
			year = year - 1
		else:
			year = 2013
		data = get_geojson_data( sig_cd, year, save = True, local_only = True )
		if len( data ) == 0:
			#print "no data from SGIS", sig_cd, area.sig_nm, year
			prev_list = [ a for a in area_info.select().where( area_info.next_area == area.id ) ]
			if len( prev_list ) > 1:
				new_geometry = { 'type': 'MultiPolygon', 'coordinates': [] }
				for prev in prev_list:
					#print "  ",prev.sig_cd
					prev_boundary_list = [ b for b in prev.boundaries ]
					if prev_boundary_list > 0 and prev_boundary_list[-1].geojson != None:
						prev_json = json.loads( prev_boundary_list[-1].geojson )
						if prev_json['type'] == 'Polygon':
							new_geometry['coordinates'].append( prev_json['coordinates'] )
						elif prev_json['type'] == 'MultiPolygon':
							new_geometry['coordinates'].extend( prev_json['coordinates'] )
				boundary.geojson = json.dumps( new_geometry, ensure_ascii = False, separators=(',', ': ') ) 
				boundary.save()
				success_count += 1
			else:
				error_count += 1
				#print "no multiple previous areas"
		else:
			j = json.loads( data )
			if len( j['features'] ) > 0:
				#print "gotcha!", sig_cd, year
				geometry = j['features'][0]['geometry']
				if geometry['type'] == "Polygon":
					geometry['coordinates'] = convert_polygon_local( geometry['coordinates'] )
				elif ( geometry['type'] == "MultiPolygon" ):
					geometry['coordinates'] = convert_multipolygon_local( geometry['coordinates'] )
				boundary.geojson = json.dumps( geometry, ensure_ascii = False, separators=(',', ': ') ) 
				boundary.save()
				success_count += 1
	return [ error_count, success_count, total_count ]


''' 시군구 이상 행정구역에 대해 선관위 관리 코드 (nec_cd) 입력 '''
def load_area_info_nec_cd( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading area_info_nec_cd"
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		nec_cd_hash = json.load( json_file )
		json_file.close()

		for elec_date in nec_cd_hash.keys():
			area_data = nec_cd_hash[elec_date]
			for sig_cd in area_data.keys():
				a = area_data[sig_cd]
				total_count += 1
				sys.stdout.write('.')
				try:	
					area = area_info.get_area_by_cd( a['sig_cd'], elec_date )
				except area_info.DoesNotExist:
					error_count += 1
					print "no such area", a['sig_cd']
					continue
				if a['sig_nm'] != area.sig_nm:
					error_count += 1
					print "name does not match!", a['sig_cd'], a['sig_nm'], area.sig_nm
					continue
				area.nec_cd = a['nec_cd']
				area.save()
				success_count += 1
	return [ error_count, success_count, total_count ]




''' 선거-선거구, 선거구-행정구역 매핑 정보 입력 ''' 
def load_elec_area_relation( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		ea_master_relation_hash = json.load( json_file )
		json_file.close()
		
		for elec_date in ea_master_relation_hash.keys():
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
			elec_area_mapping_hash = ea_master_relation_hash[elec_date]
		
			for elec_cd in elec_area_mapping_hash.keys():
				try:
					ea = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
				except elec_area_info.DoesNotExist:
					print "no such elec_area", elec_cd
					error_count += 1
					continue
				if( ea.elec_nm != elec_area_mapping_hash[elec_cd]['elec_nm'] ):
					print "elec_nm not matching", ea.elec_nm, elec_area_mapping_hash['elec_nm']
					error_count += 1
					continue
			
				if found_election:
					try:
						eearel = elec_elec_area_relation.get( ( elec_elec_area_relation.election_info == e.id ) & ( elec_elec_area_relation.elec_area_info == ea.id ) )
					except elec_elec_area_relation.DoesNotExist:
						#print "adding", e.elec_title, ea.elec_nm
						eearel = elec_elec_area_relation()
						eearel.election_info = e.id
						eearel.elec_area_info = ea.id
						eearel.save()
						success_count += 1
					else:
						pass
						#print "already exist", e.elec_title, ea.elec_nm
			
			
				area_hash = elec_area_mapping_hash[elec_cd]['area_hash']
				for sig_cd in area_hash.keys():
					total_count += 1
					sys.stdout.write('.')
					try:
						a = area_info.get_area_by_cd( sig_cd, elec_date )
						#a = area_info.get( area_info.sig_cd == sig_cd )
					except area_info.DoesNotExist:
						print "no such area", sig_cd
						error_count += 1
						continue
					if a.sig_nm != area_hash[sig_cd]:
						print "sig_nm not matching", a.sig_nm, area_hash[sig_cd]
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

''' 정당정보 입력 '''
def load_party_info( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0
	#print "loading", key
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
				total_count += 1
				sys.stdout.write('.')
				party_nm = party_data[0]
				valid_from = party_data[1]
				valid_to = party_data[2]
				if len( party_data ) > 3:
					short_nm = party_data[3]
				#party_nm, valid_from, valid_to = party_data
				try:
					party = party_info.get( ( party_info.party_nm == party_nm ) & ( party_info.valid_from == valid_from ) )
				except party_info.DoesNotExist:
					#print "new party data", party_nm, valid_from, valid_to
					party = party_info()
					party.party_nm = party_nm
					if len( party_data ) > 3:
						party.short_nm = short_nm
					party.valid_from = valid_from
					party.valid_to = valid_to
					if len( party_list ) > 0 :
						party.prev_party = party_list[-1].id
					party.save()
					if len( party_list ) > 0 :
						party_list[-1].next_party = party.id
						party_list[-1].save()
					party_list.append( party )
					success_count += 1
				else:
					pass_count += 1
					pass
					#print "already exist", party_nm, valid_from
	return [ error_count, success_count, total_count ]

''' 각 선거 후보자 정보 입력 '''
def load_candidate_info( key, basedata_config ):
	#print "loading", key
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0
	
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
				error_count += 1
				continue
						
			elec_area_candidate_hash = candidate_data_hash[elec_date]
			for elec_area_cd in elec_area_candidate_hash.keys():
				
				try:
					elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_area_cd )
				except elec_area_info.DoesNotExist:
					print "no such elec_area", elec_area_cd
					error_count += 1
					continue
				else:
					pass#print elec_area.elec_nm, elec_area.elec_cd	
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

		

''' 역대 선거 결과 입력 '''
def load_election_result( key, basedata_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0
	#print "loading", key
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
			
			#print elec.elec_title, elec.elec_date
			for elec_area_cd in result_data_hash[elec_date].keys():
				try:
					elec_area = elec_area_info.get( elec_area_info.elec_cd == elec_area_cd )
				except elec_area_info.DoesNotExist:
					print "no such elec_area!"
					continue
				#print elec_area.elec_nm
		
				vote_result = result_data_hash[elec_date][elec_area_cd]['vote_result']
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
				vote_result_list = result_data_hash[elec_date][elec_area_cd]['candidate_result']
		
				candidate_list = [ c for c in candidate_info.select().where( ( candidate_info.election_info == elec.id ) &
																											( candidate_info.elec_area_info == elec_area.id ) ) ]
		
				# 정당 및 후보자 정보 없으면 오류.
				for vote_result in vote_result_list:
					total_count += 1
					sys.stdout.write('.')
					candidate_num, party_nm, candidate_nm, sex, vote_count, vote_percent = vote_result
					#print "  ",party_nm, candidate_nm
					
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
						error_count += 1
						print "cannot find candidate", elec.elec_date, elec_area.elec_nm, candidate_num, party_nm, candidate_nm, sex
						continue

					try:
						eresult = election_result.get( ( election_result.counting_info == counting.id ) & (election_result.candidate_info == candidate.id ) )
					except election_result.DoesNotExist:
						#print "adding result", elec.elec_title, elec_area.elec_nm, candidate.person_info.name, vote_count, vote_percent
						eresult = election_result()
						eresult.counting_info = counting.id
						eresult.candidate_info = candidate.id
						eresult.vote_count = vote_count
						eresult.vote_percent = vote_percent
						eresult.save()
						success_count += 1

						# 당선자 세팅
						if max_vote < vote_count:
							max_vote = vote_count
							max_vote_result_id = eresult.id
				
				if max_vote_result_id > 0:
					eresult = election_result.get( election_result.id == max_vote_result_id )
					eresult.elected = True
					eresult.save()
	return [ error_count, success_count, total_count ]


key_list = [ 'election_info', 'elec_area_info', 'area_info', 'area_info_history', 'missing_geojson', 'area_info_nec_cd',
				'elec_area_relation', 'party_info', 'candidate_info', 'election_result' ]
for key in key_list:
	print "Loading", key
	error_count = 0
	success_count = 0
	total_count = 0
	if key == 'election_info':
		error_count, success_count, total_count = load_election_info( key, basedata_config )
	elif key == 'elec_area_info':
		error_count, success_count, total_count = load_elec_area_info( key, basedata_config )
	elif key == 'area_info':
		error_count, success_count, total_count = load_area_info( key, basedata_config )
	elif key == 'area_info_history':
		error_count, success_count, total_count = load_area_info_history( key, basedata_config )
	elif key == 'missing_geojson':
		error_count, success_count, total_count = load_missing_geojson( key, basedata_config )
	elif key == 'area_info_nec_cd':
		error_count, success_count, total_count = load_area_info_nec_cd( key, basedata_config )
	elif key == 'elec_area_relation':
		error_count, success_count, total_count = load_elec_area_relation( key, basedata_config )
	elif key == 'party_info':
		error_count, success_count, total_count = load_party_info( key, basedata_config )
	elif key == 'candidate_info':
		error_count, success_count, total_count = load_candidate_info( key, basedata_config )
	elif key == 'election_result':
		error_count, success_count, total_count = load_election_result( key, basedata_config )
	print "\nFinished loading", key, "data.\nError count:", error_count, "success count:", success_count, "total_count", total_count, "\n"
