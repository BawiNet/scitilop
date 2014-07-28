#!/usr/bin/env python
# -*- coding: utf-8 -*-

from election_class import *

def get_area_info( province_name, elec_area_name, emd_name ):
	print province_name, elec_area_name, emd_name
	try:
		parent_ea = elec_area_info.get( ( elec_area_info.elec_nm == province_name ) & ( elec_area_info.elec_lvl == 1 ) )
	except elec_area_info.DoesNotExist:
		print "cannot find province name:", province_name
		return None
	try:
		ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_area_name) & ( elec_area_info.parent_elec == parent_ea.id ) )
	except elec_area_info.DoesNotExist:
		print "cannot find election area", elec_area_name, "from province", province_name
		return None
	print "elec area id:", ea.id
	area_list = []
	try:
		for earel in elec_area_relation.select().where( elec_area_relation.elec_area_info == ea.id ):
			print earel.elec_area_info, earel.area_info
			area_list.append( earel.area_info )
			for suba in earel.area_info.children:
				area_list.append( suba )
	except elec_area_relation.DoesNotExist:
		print "no matching area for", province_name, elec_area_name, emd_name
		return None

	fullname_stack = []
	for a in area_list:
		if a.sig_nm == emd_name:
			print a.sig_nm
			fullname_stack.append( a )
			while a.parent_area != None:
				try:
					a = area_info.get( area_info.id == a.parent_area )
				except:
					pass
				fullname_stack.append( a )
			break
	return_list = []
	while( len( fullname_stack ) > 0 ):
		a = fullname_stack.pop( -1 )
		return_list.append( [ a.sig_cd, a.sig_nm ] )
	return return_list
	
#print get_area_info( u"경상남도", u"사천시남해군하동군", u"사천읍" )
