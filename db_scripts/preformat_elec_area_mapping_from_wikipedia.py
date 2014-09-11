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
import os.path
from election_class import *

import yaml
import os.path
import urllib2
from bs4 import BeautifulSoup

ea_list = elec_area_info.select().where( elec_area_info.elec_lvl == 1 )

a_list = area_info.select().where( area_info.sig_lvl == 1 )

top_hash = {}

def get_mapping_data():
    filename = "election_area_mapping.html"
    if os.path.isfile( filename ):
        f = open( filename, "r" )
        data = f.read()
        f.close()

    else: #file not exist
        url = "https://ko.wikipedia.org/wiki/%EB%8C%80%ED%95%9C%EB%AF%BC%EA%B5%AD_%EC%A0%9C19%EB%8C%80_%EA%B5%AD%ED%9A%8C%EC%9D%98%EC%9B%90_%EB%AA%A9%EB%A1%9D_(%EC%A7%80%EC%97%AD%EA%B5%AC%EB%B3%84)"

        data = urllib2.urlopen(url).read()
        f = open( filename, 'w' )
        #f = codecs.open( filename, encoding='utf-8', mode='w')
        f.write ( data )
        f.close()


    return data

def permute_elec_nm( nm_list ):
    if len( nm_list ) == 1:
        return nm_list
    l_list = nm_list[:]
    list_len = len( l_list )
    permuted_list = []
    for i in range( list_len ):
        l_list = nm_list[:]
        first_nm = l_list.pop(i)
        sub_permuted = permute_elec_nm( l_list )
        for permuted_nm in sub_permuted:
            permuted_list.append( first_nm + permuted_nm )
    return permuted_list

mapping_html = get_mapping_data()
#print mapping_html
html = BeautifulSoup( mapping_html )
#print html
table_list = html.find_all( 'table' )[1:18]
#print len( table_list )
h3_list = html.find_all( 'h3' )


area_mapping_hash = {}
top_elec_list = []
top_area_list = []


for h3 in h3_list:
    top_elec_nm = h3.span.contents[0].encode( 'utf-8' )
    try:
        ea = elec_area_info.get( elec_area_info.elec_nm == top_elec_nm )
    except elec_area_info.DoesNotExist:
        print "no such elec_area", top_elec_nm
        continue
    #area_mapping_hash[ea.elec_cd] = { 'elec_nm': top_elec_nm, 'area_hash': {} }
    top_elec_list.append( ea )

    try:
        a = area_info.get( area_info.sig_nm == top_elec_nm )
    except area_info.DoesNotExist:
        print "no such area", top_elec_nm
        continue
    top_area_list.append( a )

    #print ea.elec_cd, ea.elec_nm
json_string = ""
i = 0
for table in table_list:
    top_elec = top_elec_list[i]
    top_area = top_area_list[i]
    i+= 1
    double_row = False
    for tr in table.find_all( 'tr' ):
        l_hash = {}
        if double_row == True:
            double_row = False
            continue
        td_list = tr.find_all( 'td' )
        if len( td_list ) == 0:
            continue
        elec_nm = ""
        elec_nm_list = []
        postfix= ""
        area_list =[]
        if len( td_list ) > 0:
            if td_list[0].has_attr( 'rowspan' ):
                double_row = True
            a_list = td_list[0].find_all('a')
            if len( td_list[0].contents ) > ( len( a_list ) * 2 - 1 ): # 여러 시군구가 합쳐진 후 갑/을 등으로 나뉨
                postfix = td_list[0].contents[-1].replace( u' ', '' )
            for a in a_list:
                nm = a.contents[0]
                if nm == u'여주시':
                    nm = u'여주군'
                elec_nm += nm
                elec_nm_list.append( a.contents[0] )
            #elec_nm += postfix
        if len( td_list ) > 3:
            if len( td_list[3].contents ) > 0:
                #print td_list[3].contents[0]
                a_list = [ area.strip() for area in td_list[3].contents[0].split( ',' ) ]
                for area in a_list:
                    ta = area.split( ' ' )
                    if len( ta ) > 1:
                        area = ta[-1]
                    area_list.append( area )
                    #print area,

        else:
            pass
            #if elec_nm == u'산청군함양군거창군':
                #for td in td_list:
                    #print td
            #print elec_nm, len( td_list )
            #area_list.append( str( len( td_list ) ) )
        elec_nm = elec_nm.replace( u' ', '' )

        try:
            ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_nm + postfix ) & ( elec_area_info.parent_elec == top_elec.id ) )
        except elec_area_info.DoesNotExist:
            print "no such elec_area", elec_nm
            for elec_nm in permute_elec_nm( elec_nm_list ):
                try:
                    ea = elec_area_info.get( ( elec_area_info.elec_nm == elec_nm ) & ( elec_area_info.parent_elec == top_elec.id ) )
                except elec_area_info.DoesNotExist:
                    continue
                else:
                    break

        if len( area_list ) == 0 and len( elec_nm_list ) == 1: # 단일행정구역 선거구 - 단일 행정구역(시군구)
            nm = elec_nm_list[0]
            n_list = nm.split( u' ' )
            nm_list = [ nm, ''.join( n_list ), n_list[-1] ]
            found = False
            for nm in nm_list:
                try:
                    a = area_info.get( ( area_info.sig_nm == nm.encode( 'utf-8' ) ) & ( area_info.parent_area == top_area.id ) )
                except area_info.DoesNotExist:
                    pass
                else:
                    found = True
                    #print "no such area", nm
            if found:
                print ea.elec_cd, ea.elec_nm, a.sig_cd, a.sig_nm
                suba_list = [ a ]
            else:
                a = area_info()
                a.sig_cd = u'NotFound'
                #a.sig_nm = elec_nm_list[0].encode('utf-8' )
                suba_list.append( a )
                print "can't find area", ea.elec_cd, ea.elec_nm
        elif len( area_list ) > 0 and len( elec_nm_list ) == 1: # 단일행정구역 선거구 갑/을/.. - 복수 행정구역 (읍면동)
            nm = elec_nm_list[0]
            n_list = nm.split( u' ' )
            n_list.pop( -1 )
            nm = ''.join( n_list )

            try:
                a = area_info.get( ( area_info.sig_nm == nm.encode( 'utf-8' ) ) & ( area_info.parent_area == top_area.id ) )
            except area_info.DoesNotExist:
                print ea.elec_cd, ea.elec_nm, "no such area " + "[" + nm + "] [" + elec_nm_list[0] + "]"
                continue
            suba_list = []
            for suba in a.children:
                if suba.sig_nm in area_list:
                    suba_list.append( suba )

            if len( suba_list ) != len( area_list ):
                print "disagree!", ea.elec_cd, ea.elec_nm, "from db:", len( suba_list ), "from html", len( area_list )
                if False:
                    for suba in suba_list:
                        print suba.sig_cd, suba.sig_nm,
                    for area in area_list:
                        print area,
                    print "from db:", len( suba_list ), "from html", len( area_list )
                a = area_info()
                a.sig_cd = u'99999'
                a.sig_nm = u'Check List'
                #suba_list = [ a ]
            else:
                print ea.elec_cd, ea.elec_nm, len( area_list )
        else: # 복수행정구역 선거구 - 복수 행정구역(시군구)
            suba_list = []
            for nm in area_list:
                try:
                    a = area_info.get( ( area_info.sig_nm == nm.encode( 'utf-8' ) ) & ( area_info.parent_area == top_area.id ) )
                except area_info.DoesNotExist:
                    print ea.elec_cd, ea.elec_nm, "no such area " + "[" + nm + "]"
                    a = area_info()
                    a.sig_cd = u'NotFound'
                    a.sig_nm = nm.encode('utf-8' )
                    #suba_list.append( a )
                    #continue
                else:
                    suba_list.append( a )
            #print type( ea.elec_cd )
            print ea.elec_cd, ea.elec_nm,
            for suba in suba_list:
                print suba.sig_cd, suba.sig_nm,
            print

        if True:
            area_mapping_hash[ea.elec_cd] = { 'elec_nm': ea.elec_nm, 'area_hash' : {} }
            for suba in suba_list:
                area_mapping_hash[ea.elec_cd]['area_hash'][suba.sig_cd] = suba.sig_nm
            #json_string += json.dumps( l_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )


        #print elec_nm, ":", u','.join( area_list )
    #print table.
#tbody = table.tbody
area_mapping_json = json.dumps( area_mapping_hash, separators = (',', ':'), indent=4, sort_keys = True, encoding='utf-8', ensure_ascii=False )
#area_mapping_json_utf8 = area_mapping_json.decode( 'utf-8' )

#print json_string
f = codecs.open("area_mapping.json", encoding='utf-8', mode='w')
f.write ( area_mapping_json )
# 	f.write ( json_string )
f.close()
