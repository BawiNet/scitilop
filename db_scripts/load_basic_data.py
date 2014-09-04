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
basic_data_config = {}
basic_data_config_filename = "./basic_data_config.yaml"

if os.path.isfile( basic_data_config_filename  ):
	f = open( basic_data_config_filename, 'r')
	basic_data_config = yaml.load(f)
	f.close()

#print basic_data_config


''' 선거정보 입력 '''
def load_election_info( key, basic_data_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading election_info"
	info_type = basic_data_config['election_info']['type']
	if info_type == 'file':
		filename = basic_data_config['election_info']['location']
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

''' 행정구역 정보 입력 2014 년 기준'''
def load_area_info( key, basic_data_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading area_info"
	info_type = basic_data_config['area_info']['type']
	if info_type == 'dir':
		location = basic_data_config['area_info']['location']
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

''' 행정구역 변동내역 입력 '''
def load_area_info_history( key, basic_data_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading area_info_history"
	info_type = basic_data_config[key]['type']
	if info_type == 'file':
		filename = basic_data_config[key]['location']
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
def load_missing_geojson( key, basic_data_config ):
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
def load_area_info_nec_cd( key, basic_data_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	#print "loading area_info_nec_cd"
	info_type = basic_data_config[key]['type']
	if info_type == 'file':
		filename = basic_data_config[key]['location']
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

''' 정당정보 입력 '''
def load_party_info( key, basic_data_config ):
	error_count = 0
	success_count = 0
	total_count = 0
	pass_count = 0
	#print "loading", key
	info_type = basic_data_config[key]['type']
	if info_type == 'file':
		filename = basic_data_config[key]['location']
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

key_list = [ 'election_info', 'area_info', 'area_info_history', 'missing_geojson', 'area_info_nec_cd', 'party_info' ]

for key in key_list:
	print "Loading", key
	error_count = 0
	success_count = 0
	total_count = 0
	if key == 'election_info':
		error_count, success_count, total_count = load_election_info( key, basic_data_config )
	elif key == 'area_info':
		error_count, success_count, total_count = load_area_info( key, basic_data_config )
	elif key == 'area_info_history':
		error_count, success_count, total_count = load_area_info_history( key, basic_data_config )
	elif key == 'missing_geojson':
		error_count, success_count, total_count = load_missing_geojson( key, basic_data_config )
	elif key == 'area_info_nec_cd':
		error_count, success_count, total_count = load_area_info_nec_cd( key, basic_data_config )
	elif key == 'party_info':
		error_count, success_count, total_count = load_party_info( key, basic_data_config )
	print "\nFinished loading", key, "data.\nError count:", error_count, "success count:", success_count, "total_count", total_count, "\n"
