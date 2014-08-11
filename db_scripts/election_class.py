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
	geoJSON = TextField( null = True )
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
				parent = area_info.get( area_info.sig_cd == parent_cd )
			except area_info.DoesNotExist:
				print "no such parent area", parent_cd
				return None
			self.parent_area = parent.id
		return parent

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