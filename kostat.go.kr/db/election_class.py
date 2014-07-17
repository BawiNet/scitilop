import mysql.connector
from peewee import *

db = MySQLDatabase( user='honest', password='2volutio',
                              host='127.0.0.1',
                              database='election_info' )

class data_model( Model ):
	class Meta:
		database = db

class area_info( data_model ):
	id = IntegerField()
	sig_lvl = CharField()
	sig_cd = CharField()
	sig_nm = CharField()
	geoJSON = TextField()
	parent_id = IntegerField()
	

class election_info( data_model  ):
	id = IntegerField()
	elec_title = CharField()
	elec_lvl = CharField()
	elec_date = DateField()

class elec_area_info( data_model  ):
	id = IntegerField()
	elec_lvl = CharField()
	elec_cd = CharField()
	elec_nm = CharField()
	geoJSON = TextField()
	valid_from = DateField()
	valid_to = DateField()
	parent_id = IntegerField()

class elec_area_relation( data_model  ):
	id = IntegerField()
	elec_area_info = ForeignKeyField( elec_area_info )
	area_info = ForeignKeyField( area_info )	

class elec_elec_area_relation( data_model  ):
	id = IntegerField()
	elec_area_info = ForeignKeyField( elec_area_info )
	election_info = ForeignKeyField( election_info  )	

class party_info( data_model ):
	id = IntegerField()
	party_nm = CharField()
	valid_from = DateField()
	valid_to = DateField()
	
class person_info( data_model ):
	id = IntegerField()
	name = CharField()
	sex = CharField()
	birthdate = DateField()

class candidate_info( data_model ):
	id = IntegerField()
	candidate_num = IntegerField()
	election_info = ForeignKeyField( election_info )
	person_info = ForeignKeyField( person_info )
	party_info = ForeignKeyField( party_info )