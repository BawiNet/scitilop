#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mysql.connector
import sqlite3
from peewee import *
import sys
from datetime import date, datetime, timedelta

import yaml
import os.path
dbconfig = {}

if os.path.isfile("./dbconfig.yaml"):
	f = open("./dbconfig.yaml", 'r')
	dbconfig = yaml.load(f)
	f.close()

if 'dbname' not in dbconfig.keys():
	dbconfig['dbname'] = "election_info"
if 'dbtype' not in dbconfig.keys():
	dbconfig['dbtype'] = 'sqlite'
	
if dbconfig['dbtype'] == 'mysql':
	db = MySQLDatabase( user=dbconfig['user'], password=dbconfig['password'],
                              host=dbconfig['host'],
                              database=dbconfig['dbname'] )
	
else:
	db = SqliteDatabase('./' + dbconfig['dbname'] + '.sqlite3')


#db = MySQLDatabase( user='honest', password='2volutio',
  #                            host='127.0.0.1',
    #                          database='election_info' )

def calculate_date( a_date, daydiff ):
	y, m, d = a_date.split( "-" )
	temp_date = date( int(y), int(m), int(d) )
	timediff = timedelta( days = daydiff )
	new_date = temp_date + timediff
	return str( new_date )

class data_model( Model ):
	class Meta:
		database = db

class area_info( data_model ):
	id = PrimaryKeyField()
	sig_lvl = CharField()
	sig_cd = CharField()
	sig_nm = CharField()
	valid_from = DateField( null = True )
	valid_to = DateField( null = True )
	prev_area = ForeignKeyField( 'self', related_name = 'next', null = True )
	next_area = ForeignKeyField( 'self', related_name = 'prev',  null = True )
	parent_area = ForeignKeyField( 'self', related_name = 'children', null = True )

	def check_sig_lvl( self ):
		if len( self.sig_cd ) == 7:
			self.sig_lvl = '3'
		elif len( self.sig_cd ) == 5:
			self.sig_lvl = '2'
		elif len( self.sig_cd ) == 2:
			self.sig_lvl = '1'
		return self.sig_lvl

	def check_parent( self ) :
		if self.parent_area != None:
			return self.parent_area
		parent = None
		self.check_sig_lvl()
		if int( self.sig_lvl ) > 1:
			if len( self.sig_cd ) == 7:
				parent_cd = self.sig_cd[0:5]
			elif len( self.sig_cd ) == 5:
				parent_cd = self.sig_cd[0:2]
			else:
				return None

			try:
				parent = area_info.get( ( area_info.sig_cd == parent_cd ) & ( area_info.valid_to >= self.valid_to ) & ( area_info.valid_from <= self.valid_from ) )
			except area_info.DoesNotExist:
				print "no such parent area", parent_cd, self.valid_to, self.valid_from
				return None
			self.parent_area = parent.id
		else:
			return True
		return parent

	def check_boundary( self ):
		b_list = [ b for b in self.boundaries ]
		if len( b_list ) > 0 :
			for b in self.boundaries:
				if str( self.valid_to ) < str( b.valid_to ) and str( self.valid_to ) > str( b.valid_from ):
					b.valid_to = self.valid_to
					b.save()
				elif str( self.valid_from ) > str( b.valid_from ) and str( self.valid_to ) < str( b.valid_to ):
					b.valid_from = self.valid_from
					b.save()
		else:
			b = area_boundary_info()
			b.valid_from = self.valid_from
			b.valid_to = self.valid_to
			b.area_info = self.id
			b.save()
		return
		
	def fill_boundary( self, a_area ):
		if str( self.valid_from ) > str( a_area.valid_from ):
			next_area = self
			prev_area = a_area
		else:
			next_area = a_area
			prev_area = self
		print prev_area.sig_nm, prev_area.valid_from, prev_area.valid_to, next_area.sig_nm, next_area.valid_from, next_area.valid_to
		prev_boundary_list = [ b for b in prev_area.boundaries ]
		next_boundary_list = [ b for b in next_area.boundaries ]
		print prev_boundary_list[0].valid_from, prev_boundary_list[0].valid_to, type( prev_boundary_list[0].geojson )
		print prev_boundary_list[-1].valid_from, prev_boundary_list[-1].valid_to, type( prev_boundary_list[-1].geojson )
		print next_boundary_list[0].valid_from, next_boundary_list[0].valid_to, type( next_boundary_list[0].geojson )
		print next_boundary_list[-1].valid_from, next_boundary_list[-1].valid_to, type( next_boundary_list[-1].geojson )
		if len( prev_boundary_list ) == 0:
			b = area_boundary_info()
			b.valid_from = prev_area.valid_from
			b.valid_to = prev_area.valid_to
			b.area_info = prev_area.id
			b.save()
			prev_boundary_list.append( b )
		if len( next_boundary_list ) == 0:
			b = area_boundary_info()
			b.valid_from = next_area.valid_from
			b.valid_to = next_area.valid_to
			b.area_info = next_area.id
			b.save()
			next_boundary_list.append( b )
			
		if prev_boundary_list[-1].geojson == None and next_boundary_list[0].geojson != None:
			prev_boundary_list[-1].geojson = next_boundary_list[0].geojson
			prev_boundary_list[-1].save()
		elif prev_boundary_list[-1].geojson != None and next_boundary_list[0].geojson == None:
			next_boundary_list[0].geojson = prev_boundary_list[-1].geojson
			next_boundary_list[0].save()
		return

	def divide_boundary( self, a_date ):
		init_date = '2013-01-01' #초기 입력 데이타 기준일자 (SGIS 에서 최신이라고 가져온 자료들)

		b_list = [ b for b in self.boundaries ]
		for b in b_list:
			if str( a_date ) < str( b.valid_to ) and str( a_date ) > str( b.valid_from) :
				newb = area_boundary_info()
				if a_date > init_date:
					b.valid_to = calculate_date( a_date, -1 )
					b.save()
					newb.valid_from = a_date
					newb.valid_to = self.valid_to
				else:
					b.valid_from = a_date
					b.save()
					newb.valid_from = self.valid_from
					newb.valid_to = calculate_date( a_date, -1 )
				newb.area_info = self.id
				newb.save()
		return
	def get_boundary_geojson( self, a_date ):
		b_list = [ b for b in self.boundaries ]
		for b in b_list:
			if str( a_date ) <= str( b.valid_to ) and str( a_date ) >= str( b.valid_from) :
				return b.geojson
	@classmethod
	def get_area_by_cd( cls, a_sig_cd, a_date = ""):
		if a_date == "":
			a_date = str( date.today() )
		#print a_sig_cd, a_date
		#try:
		area = area_info.get( ( area_info.sig_cd == a_sig_cd ) & ( area_info.valid_from <a_date ) & ( area_info.valid_to > a_date ) )
		#except area_info.DoesNotExist:
			#raise
		return area

class area_boundary_info( data_model ):
	id = PrimaryKeyField()
	area_info = ForeignKeyField( area_info, related_name = 'boundaries' )
	valid_from = DateField( null = True )
	valid_to = DateField( null = True )
	geojson = TextField( null = True )
	class Meta:
		order_by = [ 'valid_from' ]

class election_info( data_model  ):
	id = PrimaryKeyField()
	elec_title = CharField()
	elec_lvl = CharField()
	elec_date = DateField()

class elec_area_info( data_model  ):
	id = PrimaryKeyField()
	elec_lvl = CharField()
	elec_cd = CharField()
	elec_nm = CharField()
	geoJSON = TextField( null = True )
	valid_from = DateField( null = True )
	valid_to = DateField( null = True )
	prev_elec = ForeignKeyField( 'self', related_name = 'next', null = True )
	next_elec = ForeignKeyField( 'self', related_name = 'prev', null = True )
	parent_elec = ForeignKeyField( 'self', related_name = 'children', null = True )

	def get_emd_list( self ):
		area_list = []
		try:
			earel = elec_area_relation.select().where( elec_area_relation.elec_area_info == self.id )
		except:
			return area_list
		#print earel
		for ea in earel:
			#print ea
			area = ea.area_info
			#print area.sig_nm, area.sig_lvl, type( area.sig_lvl )
			
			if int( area.sig_lvl ) == 3:
				#print "added", area.sig_nm
				area_list.append( area )
			elif int( area.sig_lvl )== 2:
				#print "added sub", area.sig_nm
				area_list.extend( area.children )
		#print area_list
		return area_list
			

class elec_area_relation( data_model  ):
	id = PrimaryKeyField()
	elec_area_info = ForeignKeyField( elec_area_info )
	area_info = ForeignKeyField( area_info )	

class elec_elec_area_relation( data_model  ):
	id = PrimaryKeyField()
	elec_area_info = ForeignKeyField( elec_area_info )
	election_info = ForeignKeyField( election_info  )	

class party_info( data_model ):
	id = PrimaryKeyField()
	party_nm = CharField()
	wikipedia_link = CharField( null = True )
	valid_from = DateField()
	valid_to = DateField()
	prev_party = ForeignKeyField( 'self', related_name = 'succeeded_by', null = True )
	next_party = ForeignKeyField( 'self', related_name = 'preceded_by', null = True )
	
class person_info( data_model ):
	id = PrimaryKeyField()
	name = CharField()
	hanja = CharField( null = True )
	wikipedia_link = CharField( null = True )
	sex = CharField()
	birthdate = DateField( null = True )

class candidate_info( data_model ):
	id = PrimaryKeyField()
	candidate_num = IntegerField()
	election_info = ForeignKeyField( election_info )
	elec_area_info = ForeignKeyField( elec_area_info )
	person_info = ForeignKeyField( person_info )
	party_info = ForeignKeyField( party_info )

class counting_info( data_model ):
	id = PrimaryKeyField()
	election_info = ForeignKeyField( election_info )
	elec_area_info = ForeignKeyField( elec_area_info )
	area_info = ForeignKeyField( area_info, null = True )
	station_id = CharField( null = True )
	counting_time = DateTimeField( null = True )
	counting_percent = FloatField( default = 0 )
	eligible_count = IntegerField( default = 0 )
	vote_count = IntegerField( default = 0 )
	invalid_count = IntegerField( default = 0 )
	abstention_count = IntegerField( default = 0 )

class election_result( data_model ):
	id = PrimaryKeyField()
	counting_info = ForeignKeyField( counting_info )
	candidate_info = ForeignKeyField( candidate_info )
	vote_count = IntegerField( default = 0 )
	vote_percent = FloatField( default = 0 )
	elected = BooleanField( default = False )