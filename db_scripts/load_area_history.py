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
from datetime import timedelta, datetime

filename = "area_info_history.json"
json_file = open( filename, 'r' )
area_info_history_hash = json.load( json_file )
json_file.close()
for change_date in area_info_history_hash.keys():
	changes_list = area_info_history_hash[change_date]
	print change_date
	for change in changes_list:
		print change['sig_cd']
		new_cd = change['sig_cd']
		if change['type'] == u'신설':
			try:
				area = area_info.get( area_info.sig_cd == new_cd )
			except area_info.DoesNotExist:
				print "adding new area_info", new_cd, change['sig_nm']
				area = area_info()
				area.sig_cd = new_cd
				area.sig_nm = change['sig_nm']
				area.valid_to = "9999-12-31"
			else:
				print "updating area_info that already exists", new_cd, change['sig_nm']
				#continue
			area.valid_from = change_date
			area.check_sig_lvl()
			parent = area.check_parent()
			if parent == None:
				print "no parent for", area.sig_cd
				continue
			area.save()
		elif change['type'] == u'변경':
			try:
				area = area_info.get( area_info.sig_cd == new_cd )
				print "updating area_info", new_cd, change['sig_nm']
			except area_info.DoesNotExist:
				print "adding new area_info", new_cd, change['sig_nm']
				area = area_info()
				area.sig_cd = new_cd
				area.sig_nm = change['sig_nm']
				area.valid_to = "9999-12-31"
				sig_lvl = area.check_sig_lvl()
				parent = area.check_parent()
				if parent == None:
					print "no parent for", area.sig_cd
					continue
			area.valid_from = change_date
			area.save()

			try:
				prev_area = area_info.get( area_info.sig_cd == change['prev_cd'] )
				print "updating area_info", change['prev_cd'], change['prev_nm']
			except area_info.DoesNotExist:
				print "adding new area_info", change['prev_cd'], change['prev_nm']
				prev_area = area_info()
				prev_area.sig_cd = change['prev_cd']
				prev_area.sig_nm = change['prev_nm']
				prev_area.valid_from = "1948-08-15"
				sig_lvl = prev_area.check_sig_lvl()
				parent = prev_area.check_parent()
				if parent == None:
					print "no parent for", prev_area.sig_cd
					continue
			
			prev_area.valid_to = calculate_date( change_date, -1 )
			prev_area.next_area = area.id

			if prev_area.geoJSON == None and area.geoJSON != None:
				prev_area.geoJSON = area.geoJSON
			prev_area.save()
			
			area.prev_area = prev_area.id
			if area.geoJSON == None and prev_area.geoJSON != None:
				area.geoJSON = prev_area.geoJSON
			area.save()

		elif change['type'] == u'분리':
			print u"분리"
			try:
				prev_area = area_info.get( area_info.sig_cd == change['prev_cd'] )
			except area_info.DoesNotExist:
				prev_area = area_info()
				prev_area.sig_cd = change['prev_cd']
				prev_area.sig_nm = change['prev_nm']
				prev_area.valid_from = "1948-08-15"
				sig_lvl = prev_area.check_sig_lvl()
				parent = prev_area.check_parent()
				if parent == None:
					print "no parent for", prev_area.sig_cd
					continue
			prev_area.valid_to = calculate_date( change_date, -1 )
			prev_area.next_area = None
			prev_area.save()

			try:
				area = area_info.get( area_info.sig_cd == new_cd )
			except area_info.DoesNotExist:
				area = area_info()
				area.sig_cd = new_cd
				area.sig_nm = change['sig_nm']
				area.valid_to = "9999-12-31"
				sig_lvl = area.check_sig_lvl()
				parent = area.check_parent()
				if parent == None:
					print "no parent for", area.sig_cd
					continue
			area.valid_from = change_date
			area.prev_area = prev_area.id
			area.save()

		elif change['type'] == u'통합':
			print u"통합"
			try:
				area = area_info.get( area_info.sig_cd == new_cd )
			except area_info.DoesNotExist:
				area = area_info()
				area.sig_cd = new_cd
				area.sig_nm = change['sig_nm']
				area.valid_to = "9999-12-31"
				sig_lvl = area.check_sig_lvl()
				parent = area.check_parent()
				if parent == None:
					print "no parent for", area.sig_cd
					continue
			area.valid_from = change_date
			area.prev_area = None
			area.save()

			try:
				prev_area = area_info.get( area_info.sig_cd == change['prev_cd'] )
			except area_info.DoesNotExist:
				prev_area = area_info()
				prev_area.sig_cd = change['prev_cd']
				prev_area.sig_nm = change['prev_nm']
				prev_area.valid_from = "1948-08-15"
				sig_lvl = prev_area.check_sig_lvl()
				parent = prev_area.check_parent()
				if parent == None:
					print "no parent for", prev_area.sig_cd
					continue
			prev_area.valid_to = calculate_date( change_date, -1 )
			prev_area.next_area = area.id
			prev_area.save()
		elif change['type'] == u'폐지':
			print u"폐지"
			try:
				area = area_info.get( area_info.sig_cd == new_cd )
			except area_info.DoesNotExist:
				area = area_info()
				area.sig_cd = new_cd
				area.sig_nm = change['sig_nm']
				area.valid_from = "1948-08-15"
			sig_lvl = area.check_sig_lvl()
			parent = area.check_parent()
			if parent == None:
				print "no parent for", area.sig_cd
				continue
			area.valid_to = calculate_date( change_date, -1 )
			area.save()
			

		#break