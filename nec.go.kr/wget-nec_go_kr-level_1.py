#!/usr/bin/env python
import os
import sys
import string
import urllib
import time
from BeautifulSoup import BeautifulSoup

filename_list = 'election_info.presidential.txt'

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

## Variables
## $election_type, $election_code, $city_code
#url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0000000000&requestURI=%2Felectioninfo%2F0000000000%2Fvc%2Fvccp09.jsp&statementId=VCCP02_%231&electionName=$election_code&electionCode=$election_type&cityCode=$city_code')
url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.xhtml?electionId=0000000000&requestURI=%2Felectioninfo%2F0000000000%2Fvc%2Fvccp09.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP09&statementId=VCCP02_%2391&oldElectionType=0&electionType=$election_type&electionName=$election_code&electionCode=$election_type&cityCode=$city_code')

city_code_list = []
f_region = open('city_town_code.txt','r')
for line in f_region:
    tokens = line.strip().split("\t")
    city_code = tokens[0]
    town_code = tokens[1]
    city_code_list.append(city_code)
f_region.close()

for tmp_name in sorted(elections.keys(),reverse=True):
    if( not tmp_name.startswith('presidential.20') ):
        continue

    for city_code in list(set(city_code_list)):
        ## Before 2007
        city_code = city_code.replace('00','')

        tmp_e_type = elections[tmp_name]['type']
        tmp_e_code = elections[tmp_name]['code']
        tmp_var = {'election_code':tmp_e_code, 'election_type':tmp_e_type,'city_code':city_code}
        tmp_url = url_template.substitute(tmp_var)
        f_url = urllib.urlopen(tmp_url)
        tmp_content = f_url.read()
        f_url.close()
        filename_out = 'html_1/%s.%s.html'%(tmp_name,city_code)
        sys.stderr.write('Write %s ... '%filename_out)
        f_out = open(filename_out,'w')
        soup = BeautifulSoup(tmp_content)
        f_out.write(soup.prettify())
        f_out.close()
        sys.stderr.write('Done\n')
        time.sleep(3)
f_region.close()
