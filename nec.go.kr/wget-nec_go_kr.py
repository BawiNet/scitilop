#!/usr/bin/env python
import os
import sys
import string
import urllib
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
## $election_type, $election_code, $city_code, $town_code
url_template = string.Template('http://info.nec.go.kr/electioninfo/electionInfo_report.action?electionId=0000000000&requestURI=%2Felectioninfo%2F0000000000%2Fvc%2Fvccp08.jsp&topMenuId=VC&secondMenuId=VCCP&menuId=VCCP08&statementId=VCCP08_%233&oldElectionType=$election_type&electionType=$election_type&electionName=%s&electionCode=$election_code&cityCode=$city_code&townCode=$town_code')

f_region = open('city_town_code.txt','r')
for line in f_region:
    tokens = line.strip().split("\t")
    city_code = tokens[0]
    town_code = tokens[1]
    for tmp_name in sorted(elections.keys()):
        tmp_e_type = elections[tmp_name]['type']
        tmp_e_code = elections[tmp_name]['code']
        tmp_var = {'election_code':tmp_e_code, 'election_type':tmp_e_type,'city_code':city_code,'town_code':town_code}
        tmp_url = url_template.substitute(tmp_var)
        f_url = urllib.urlopen(url_template.substitute(tmp_var))
        tmp_content = f_url.readlines()
        f_url.close()
        filename_out = 'html/%s.%s.%s.html'%(tmp_name,city_code,town_code)
        sys.stderr.write('Write %s ... '%filename_out)
        f_out = open(filename_out,'w')
        soup = BeautifulSoup(tmp_content)
        f_out.write(soup.prettify())
        f_out.close()
        sys.stderr.write('Done\n')
        break
    break
f_region.close()
