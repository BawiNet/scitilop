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
		elec_area_hash = json.load( json_file )
		json_file.close()
		for elec_cd in elec_area_hash.keys():
			elec_data = elec_area_hash[elec_cd]
			try:
				ea = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
				
			except elec_area_info.DoesNotExist:
				print "new elec_area data", elec_cd, elec_data
				ea = elec_area_info()
				ea.elec_cd = elec_cd
				ea.elec_lvl, ea.elec_nm = elec_data
				ea.valid_from = "2014-01-01"
				ea.valid_to = "9999-12-31"
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
				sig_lvl = elems[3]
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
						print "new data", data['properties']['Name'], data['properties']['Description']
						area = area_info()
						area.sig_cd = data['properties']['Name']
						area.sig_nm = data['properties']['Description']
						area.geoJSON = json.dumps( data['geometry'], ensure_ascii = False, separators=(',', ': ') ) 
						area.valid_from = "2014-01-01"
						area.valid_to = "9999-12-31"
						area.coord_sys = "WGS84"
						area.sig_lvl = sig_lvl
						if sig_lvl == '2':
							try:
								parent = area_info.get( area_info.sig_cd == area.sig_cd[0:2] )
								area.parent_id = parent.id
							except area_info.DoesNotExist:
								print "no parent area"
						elif sig_lvl == '3':
							try:
								parent = area_info.get( area_info.sig_cd == area.sig_cd[0:5] )
								area.parent_id = parent.id
							except area_info.DoesNotExist:
								print "no parent area"
						area.save()


''' 선거-선거구 매핑 정보 입력 ''' 

key = 'elec_elec_area_relation'
if key in basedata_config.keys():
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


''' 선거구-행정구역 매핑 정보 입력 ''' 

key = 'elec_area_relation'
if key in basedata_config.keys():
	print "loading", key
	info_type = basedata_config[key]['type']
	if info_type == 'file':
		filename = basedata_config[key]['location']
		json_file = open( filename, 'r' )
		ea_relation_hash = json.load( json_file )
		json_file.close()
		for elec_cd in ea_relation_hash.keys():
			sig_cd_list = ea_relation_hash[elec_cd]
			try:
				ea = elec_area_info.get( elec_area_info.elec_cd == elec_cd )
			except elec_area_info.DoesNotExist:
				print "no such elec area", elec_cd
			else:
				for sig_cd in sig_cd_list:
					try:
						area = area_info.get( area_info.sig_cd == sig_cd )
					except area_info.DoesNotExist:
						print "no such area", sig_cd
					else:	
						try:
							earel = elec_area_relation.get( ( elec_area_relation.elec_area_info == ea.id ) & ( elec_area_relation.area_info == area.id ) )
						except elec_area_relation.DoesNotExist:
							print "adding elec_area_relation", elec_cd, sig_cd
							earel = elec_area_relation()
							earel.elec_area_info = ea.id
							earel.area_info = area.id
							earel.save()
						else:
							print "already exist", elec_cd, sig_cd, earel.id
