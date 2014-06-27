#!/usr/bin/env python
import os
import sys
import string
import urllib
import time
from BeautifulSoup import BeautifulSoup

filename_list = 'election_info.legislative.txt'

election_title = filename_list.split('.')[1]

elections = dict()
f_list = open(filename_list,'r')
for line in f_list:
    tokens = line.strip().split("\t")
    tmp_election_type = tokens[0]
    tmp_election_code = tokens[1]
    tmp_election_order = tokens[2]

    tmp_election_name = '%s.%s'%(election_title, tmp_election_code)
    elections[ tmp_election_name ] = {'type':tmp_election_type, 'code':tmp_election_code}
f_list.close()

## Variables - $election_type, $election_code, $city_code, $town code

## Election result
#url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0000000000&requestURI=%2Felectioninfo%2F0000000000%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP02_%2391&oldElectionType=&electionType=$election_type&electionName=$election_code&electionCode=$election_type&cityCode=$city_code')

## Election result - 19th
#out_type = 'result'
#url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0020120411&requestURI=%2Felectioninfo%2F0020120411%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP09_%232&electionCode=2&cityCode=$city_code')

## Progress - 195h
out_type = 'progress'
url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.action?electionId=0020120411&requestURI=%2Felectioninfo%2F0020120411%2Fvc%2Fvcvp01.jsp&topMenuId=VC&secondMenuId=VCVP&menuId=VCVP01&statementId=VCVP01_%232&sggTime=20%EC%8B%9C&cityCode=$city_code&timeCode=0&x=47&y=6')

## Candidates
## Candidates
#url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0000000000&requestURI=%2Felectioninfo%2F0000000000%2Fcp%2Fcpri03.jsp&topMenuId=CP&secondMenuId=CPRI03&menuId=&statementId=CPRI03_%231&oldElectionType=1&electionType=$election_type&electionName=$election_code&electionCode=2&cityCode=$city_code&proportionalRepresentationCode=-1&sggCityCode=-1&townCode=-1&sggTownCode=0&dateCode=0&x=35&y=12')

## Voters
#url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0000000000&requestURI=%2Felectioninfo%2F0000000000%2Fbi%2Fbipb02.jsp&topMenuId=BI&secondMenuId=BIPB&menuId=BIPB02&statementId=BIPB02_%239&oldElectionType=1&electionType=$election_type&electionName=$election_code&searchType=5&electionCode=-1&cityCode=$city_code&townCode=$town_code&sggCityCode=-1&x=24&y=17')

city_code_list = []
city2town = dict()
f_region = open('city_town_code.txt','r')
for line in f_region:
    tokens = line.strip().split("\t")
    city_code = tokens[0]
    town_code = tokens[1]
    city_code_list.append(city_code)
    if( not city2town.has_key(city_code) ):
        city2town[city_code] = []
    city2town[city_code].append(town_code)
f_region.close()

for tmp_name in sorted(elections.keys(),reverse=True):
    for city_code in list(set(city_code_list)):
        #city_code = city_code.replace('00','')

        tmp_e_type = elections[tmp_name]['type']
        tmp_e_code = elections[tmp_name]['code']
        if( tmp_e_code != '20120411' ):
            continue

        #tmp_var = {'election_code':tmp_e_code, 'election_type':tmp_e_type,'city_code':city_code, 'town_code':town_code}
        tmp_var = {'election_code':tmp_e_code, 'election_type':tmp_e_type,'city_code':city_code}
        tmp_url = url_template.substitute(tmp_var)
        sys.stderr.write('URL: %s\n'%tmp_url)
        f_url = urllib.urlopen(tmp_url)
        tmp_content = f_url.read()
        f_url.close()
        #filename_out = 'legislative.raw/voters.%s.%s.html'%(tmp_name,city_code)
        filename_out = 'legislative.raw/%s.%s.%s.html'%(out_type,tmp_name,city_code)
        sys.stderr.write('Write %s ... '%filename_out)
        f_out = open(filename_out,'w')
        soup = BeautifulSoup(tmp_content)
        f_out.write(soup.prettify())
        f_out.close()
        sys.stderr.write('Done\n')
        time.sleep(3)
    f_region.close()
