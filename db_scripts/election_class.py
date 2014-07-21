import mysql.connector
import sqlite3
from peewee import *
import sys

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

class data_model( Model ):
	class Meta:
		database = db

class area_info( data_model ):
	id = PrimaryKeyField()
	sig_lvl = CharField()
	sig_cd = CharField()
	sig_nm = CharField()
	geoJSON = TextField()
	prev_area = ForeignKeyField( 'self', related_name = 'next', null = True )
	next_area = ForeignKeyField( 'self', related_name = 'prev',  null = True )
	parent = ForeignKeyField( 'self', related_name = 'children', null = True )
	

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
	valid_from = DateField()
	valid_to = DateField()
	prev_elec = ForeignKeyField( 'self', related_name = 'next', null = True )
	next_elec = ForeignKeyField( 'self', related_name = 'prev', null = True )
	parent_id = ForeignKeyField( 'self', related_name = 'children', null = True )

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
	counting_time = DateTimeField( null = True )
	counting_percent = FloatField()
	vote_count = IntegerField()
	invalid_count = IntegerField()

class election_result( data_model ):
	id = PrimaryKeyField()
	counting_info = ForeignKeyField( counting_info )
	candidate_info = ForeignKeyField( candidate_info )
	vote_count = IntegerField()
	vote_percent = FloatField()
	elected = BooleanField( default = False )