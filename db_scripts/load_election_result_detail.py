#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import gzip
import json
import os
import sys
#import mysql.connector
from datetime import date, datetime, timedelta
from peewee import *
import string
import codecs
import os.path
from election_class import *

import yaml
import os.path

location = "../nec.go.kr/legislative.2012"

elec_date = '2012-04-11'
election_result_hash = {}
election_result_hash[elec_date] = {}
try:
	election = election_info.get( election_info.elec_date == elec_date )
except election_info.DoesNotExist:
	print "no such election", elec_date
	

for dirname, dirnames, filenames in os.walk( location ):
	for filename in filenames:
		print filename
		elems = filename.split( "." )
		if elems[-1] != 'txt':
			continue
		top_sig_cd = elems[1]
		try:
			top_area = area_info.get( area_info.sig_cd == top_sig_cd )
		except area_info.DoesNotExist:
			print "no such top area", top_sig_cd
			continue
		try:
			top_ea = elec_area_info.get( elec_area_info.elec_nm == top_area.sig_nm )
		except area_info.DoesNotExist:
			print "no such top elec_area", top_area.sig_nm
			continue
					
		datatype = elems[2]
		fullpath = os.path.join(dirname, filename)	
		f = codecs.open(fullpath, encoding='utf-8')
		#f = open( fullpath, "r" )
		result_data = f.read()
		f.close()
		ea = None
		area = None
		lines = result_data.split( '\n' )
		#print fullpath
		#print "total line", len( lines )
		for line in lines:
			#print "["+line+"]"
			line.strip()
			#print "["+line[0]+"]"
			if len( line ) > 0 and line[0] == '#':
				#print "next line"
				continue
			#print line
			#print line[0]
			data_list = line.split( '\t' )
			#print data_list
			if len( data_list ) != 6 and len( data_list ) != 7:
				continue
			if datatype == 'main':
				sido_nm, elec_nm, sig_nm, station_id, party_nm, name, vote_count = data_list
			elif datatype == 'extra':
				try:
					sido_nm, elec_nm, sig_nm, station_id, count_title, count = data_list
				except ValueError:
					print line
					break
			else:
				continue
			
			''' 세종자치시 관련 처리. 2012 년 7 월에 행정구역이 정리되었으므로 그 이전은 연기군/공주시/청원군 등으로 처리해야 함 '''
			if sido_nm == u'세종특별자치시':
				if sig_nm.find( u'연기군' ) > -1 :
					sig_nm = sig_nm.replace( u'연기군 ', u'' )
			''' 벌용동 -> 벌룡동, 팔용동 -> 팔룡동 '''
			if sig_nm == u'벌용동':
				sig_nm = u'벌룡동'
			if sig_nm == u'팔용동':
				sig_nm = u'팔룡동'

			if sido_nm != top_area.sig_nm:
				print "warning: sido_nm", sido_nm, "does not match top_area name", top_area.sig_nm, "of", top_sig_cd

			#if ea == None or ea.elec_nm != elec_nm:
			try:
				ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_nm ) & ( elec_area_info.parent_elec == top_ea.id ) )
			except elec_area_info.DoesNotExist:
				print "cannot find elec_area with name", elec_nm
				continue
			area_id = None
			sig_nm_list = []
			#area_found = False
			if sig_nm == u'NA':
				if station_id == u'NA':
					temp_list = count_title.split( u'_' )
					if len( temp_list ) == 2 :
						station_id, count_title = temp_list
				#pass
				#부재자 투표 등 처리
			else:	
				sig_nm_list.append( sig_nm )
				if sig_nm.find( u'·' ) > -1:
					sig_nm_list.append( sig_nm.replace( u'·', u',' ) )
				if sig_nm.find( u',' ) > -1:
					sig_nm_list.append( sig_nm.replace( u',', u'·' ) )
				m = re.search( ur'제(\d+)', sig_nm )
				if m:
					sig_nm_2 = re.sub( ur'제(\d+)', r'\1', sig_nm )
					sig_nm_list.append( sig_nm_2 )

				emd_list = []
				#if area == None or area.sig_nm  not in sig_nm_list:
				area_list = []
				area_found = False
				
				emd_list = ea.get_emd_list()
				#print "emd_list", emd_list
				for emd in emd_list:
					if emd.sig_nm in sig_nm_list:
						#print emd.sig_nm, 
						#for s in sig_nm_list:
						#	print s,
						#print
						area_found = True
						sig_nm = emd.sig_nm
						area = emd
						break
				#print "area found:", area_found
	
				if area_found == False:
					print "area not found:", sido_nm, elec_nm, sig_nm, station_id
					#for emd in emd_list:
					#	print emd.sig_nm, 
					#	for s in sig_nm_list:
					#		print s,
					#	print
					area_id = None
				else:
					#print "area found", area_found
					area_id = area.id

			#election_result_hash[elec_date][ea.elec_cd] = {}
			#election_result_hash[elec_date][ea.elec_cd][area.sig_cd] = {}
			#election_result_hash[elec_date][ea.elec_cd][station_id] = {}
			#election_result_hash[elec_date][ea.elec_cd][station_id]['vote_result'] = []
			#election_result_hash[elec_date][ea.elec_cd][station_id]['candidate_result'] = []


			try:
				counting = counting_info.get( ( counting_info.election_info == election.id ) & 
																( counting_info.elec_area_info == ea.id ) & 
																( counting_info.area_info == area_id ) & 
																(counting_info.station_id == station_id ) )
																
				'''c_list = [ c for c in counting ]
				if len( c_list ) == 1:
					candidate = c_list[0]
				elif len( c_list ) > 1 :
					print "more than one counting info", election.elec_date, ea.elec_nm, area_id, station_id'''
			except counting_info.DoesNotExist:
				print "addign counting_info", sido_nm, elec_nm, sig_nm, station_id
				counting = counting_info()
				counting.election_info = election.id
				counting.elec_area_info = ea.id
				counting.area_info = area_id
				counting.station_id = station_id
				counting.counting_percent = 100
				counting.save()
				
			if datatype == 'main':
#서울특별시	강남구갑	논현1동	논현1동제3투	무소속	권헌성	24
				try:
					party = party_info.get( ( party_info.party_nm == party_nm ) & ( party_info.valid_from < elec_date ) & ( party_info.valid_to > elec_date ) )
				except party_info.DoesNotExist:
					print "no such party", party_nm
					party = party_info()
					party.party_nm = party_nm
					party.valid_from = elec_date
					party_valid_to = '9999-12-31'
					party.save()
				try:
					candidate = candidate_info.select().join( person_info ).where( ( candidate_info.party_info == party.id ) & 
																													( person_info.name == name ) & 
																													( candidate_info.elec_area_info == ea.id ) &
																													( candidate_info.election_info == election.id ) )
					c_list = [ c for c in candidate ]
					if len( c_list ) == 1:
						#print "one candidate info", election.elec_date, ea.elec_nm, area_id, station_id, name
						candidate = c_list[0]
					elif len( c_list ) > 1 :
						print "more than one candidate  info", election.elec_date, ea.elec_nm, area_id, station_id, name
					elif len( c_list ) == 0 :
						print "no candidate info", election.elec_date, ea.elec_nm, area_id, station_id, name
						continue
				except candidate_info.DoesNotExist:
					print "can't find candidate", party_nm, name
					person_list = []
					try:
						person = person_info.get( person_info.name == name )
					except person_info.DoesNotExist:
						print "adding person_info", name
						person = person_info()
						person.name = name
						person.save()
					candidate = candidate_info()
					candidate.party_info = party.id
					candidate.person_info = person.id
					candidate.election_info = election.id
					candidate.elec_area_info = ea.id
					candidate.save()
				try:
					#print candidate, counting
					eresult = election_result.get( ( election_result.candidate_info == candidate.id ) & ( election_result.counting_info == counting.id ) )
				except election_result.DoesNotExist:
					print "adding election_result", sido_nm, elec_nm, sig_nm, station_id, party_nm, name, vote_count
					eresult = election_result()
					eresult.candidate_info = candidate.id
					eresult.counting_info = counting.id
					eresult.vote_count = vote_count
					eresult.save()
			else:#선거권자 투표수 무효 기권
				if count_title == u'선거권자':
					counting.eligible_count += int( count )
				elif count_title == u'투표수':
					counting.vote_count += int( count )
				elif count_title == u'무효' :
					counting.invalid_count += int( count )
				elif count_title == u'기권':
					counting.abstention_count += int( count )
				counting.save()
