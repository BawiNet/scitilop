#-*- coding: utf-8 -*-
import os
import sys
import codecs

area_code = dict()
filename_code = os.path.join('..','..','kostat.go.kr','region_code.1.txt')
f_code = codecs.open(filename_code,'r','utf-8')
for line in f_code:
    tokens = line.strip().split("\t")
    area_code[ tokens[2].encode('utf-8') ] = int(tokens[0])
f_code.close()    

tag_fileinfo = u'[국회의원선거]'
tag_candidate = u"투표수"
tag_remote_abroad = u'국외부재자투표'
tag_remote_domestic = u'국내부재자투표'
tag_wrong_ballot = u'잘못투입된투표지'
tag_sum = u'계'

def parse_xlstxt(filename):
    idx = 0
    province_name = 'NA'
    city_name = 'NA'
    candidates = []
    remotes_abroad = dict()
    remotes_domestic = dict()
    votes_district = dict()
    
    tmp_loc = 0     ## 0: nothing, 1: candidate, 2:votes
    town_name = 'NA'
    f = codecs.open(filename,'r','utf-8')
    for line in f:
        tokens = line.strip().replace(',','').split("\t")
        #print type(tokens[0].encode('utf-8'))
        #print repr(tokens[0].encode('utf-8'))
        #print repr(tag_loc1)

        if( tokens[0].startswith(tag_fileinfo) ):
            (province_name, city_name) = tokens[-1].split('][')
            province_name = province_name.replace('[','')
            city_name = city_name.replace(']','')

        if( tokens[0].startswith(tag_candidate) ):
            tmp_loc = 1
            continue
        elif( tokens[0].startswith(tag_remote_abroad) ):
            remotes_abroad = {'voter':int(tokens[2]), \
                                'ballot':int(tokens[3]),\
                                'province':province_name,\
                                'city':city_name,\
                                'town':town_name,\
                                'vote_list':tokens[2:-3], \
                                'candidates':candidates,\
                                'invalid':int(tokens[-2]), \
                                'abstention':int(tokens[-1]) }
            continue
        elif( tokens[0].startswith(tag_remote_domestic ) ):
            remotes_domestic = {'voter':int(tokens[2]), \
                                'ballot':int(tokens[3]),\
                                'province':province_name,\
                                'city':city_name,\
                                'town':town_name,\
                                'vote_list':tokens[2:-3], \
                                'candidates':candidates,\
                                'invalid':int(tokens[-2]), \
                                'abstention':int(tokens[-1]) }
            tmp_loc = 2
            continue
        
        if( tokens[0] == '' or tokens[0].startswith(tag_sum) ):
            tmp_loc = 0
            continue
        if( tokens[0].startswith(tag_wrong_ballot) ):
            tmp_loc = 0
            continue
        
        if( tmp_loc == 0 ):
            continue
        elif( tmp_loc == 1 ):
            candidates += tokens
        elif( tmp_loc == 2 ):
            if( len(tokens) == 17 ):
                town_name = tokens[0]
                continue
            elif( len(tokens) == 16 ):
                district_name = tokens[0]
                votes_district[district_name] = {'voter':int(tokens[1]), \
                                'ballot':int(tokens[2]),\
                                'province':province_name,\
                                'city':city_name,\
                                'town':town_name,\
                                'vote_list':tokens[3:-3], \
                                'candidates':candidates,\
                                'invalid':int(tokens[-2]), \
                                'abstention':int(tokens[-1]) }
    f.close()
    return remotes_abroad, remotes_domestic, votes_district

f_out = dict()
f_extra = dict()

dirname_txt = u'2012.txt'
for filename in os.listdir(dirname_txt):
    if( not filename.endswith('.xls.txt') ):
        continue

    province_name = filename.split('_')[1].encode('utf-8')
    filename_main = 'legislative2012.%s.main.txt'%area_code[province_name]
    filename_extra = 'legislative2012.%s.extra.txt'%area_code[province_name]
    if( not f_out.has_key(province_name) ):
        f_out[province_name] = codecs.open(filename_main,'w','utf-8')
        f_out[province_name].write('#%s\t%s\t%s\t%s\t%s\t%s\t%s\n'%(u'특별시/광역시/도',u'시군구',u'읍면동',u'선거구',u'후보정당',u'후보',u'득표수'))
        f_extra[province_name] = codecs.open(filename_extra,'w','utf-8')
        f_extra[province_name].write('#%s\t%s\t%s\t%s\t%s\t%s\n'%(u'특별시/광역시/도',u'시군구',u'읍면동',u'선거구',u'항목',u'항목값'))
    
    sys.stderr.write(filename+' -> '+filename_main+'\n')
    (rv_remotes_abroad, rv_remotes_domestic, rv_votes_district) \
        = parse_xlstxt(os.path.join(dirname_txt,filename))

    rv2 = rv_remotes_abroad
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv2['province'],rv2['city'],rv2['town'],u'국외부재자_선거권자',rv2['voter']))
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv2['province'],rv2['city'],rv2['town'],u'국외부재자_투표수',rv2['ballot']))
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv2['province'],rv2['city'],rv2['town'],u'국외부재자_무효',rv2['invalid']))
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv2['province'],rv2['city'],rv2['town'],u'국외부재자_기권',rv2['abstention']))

    rv3 = rv_remotes_domestic
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv3['province'],rv3['city'],rv3['town'],u'국내부재자_선거권자',rv3['voter']))
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv3['province'],rv3['city'],rv3['town'],u'국내부재자_투표수',rv3['ballot']))
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv3['province'],rv3['city'],rv3['town'],u'국내부재자_무효',rv3['invalid']))
    f_extra[province_name].write('%s\t%s\t%s\tNA\t%s\t%d\n'%(rv3['province'],rv3['city'],rv3['town'],u'국내부재자_기권',rv3['abstention']))

    for district_name in rv_votes_district.keys():
        rv1 = rv_votes_district[district_name]
        f_extra[province_name].write('%s\t%s\t%s\t%s\t%s\t%d\n'%(rv1['province'],rv1['city'],rv1['town'],district_name,u'선거권자',rv1['voter']))
        f_extra[province_name].write('%s\t%s\t%s\t%s\t%s\t%d\n'%(rv1['province'],rv1['city'],rv1['town'],district_name,u'투표수',rv1['ballot']))
        f_extra[province_name].write('%s\t%s\t%s\t%s\t%s\t%d\n'%(rv1['province'],rv1['city'],rv1['town'],district_name,u'무효',rv1['invalid']))
        f_extra[province_name].write('%s\t%s\t%s\t%s\t%s\t%d\n'%(rv1['province'],rv1['city'],rv1['town'],district_name,u'기권',rv1['abstention']))

        candidate_list = []
        for i in range(0,len(rv1['candidates']),2):
            candidate_list.append( '%s\t%s'%(rv1['candidates'][i],rv1['candidates'][i+1]) )
        
        idx = 0
        for tmp_candidate in candidate_list:
            f_out[province_name].write('%s\t%s\t%s\t%s\t%s\t%s\n'%(rv1['province'],rv1['city'],rv1['town'],district_name,tmp_candidate,rv1['vote_list'][idx]))
            idx += 1
    
    idx = 0
    for tmp_candidate in candidate_list:
        f_out[province_name].write('%s\t%s\t%s\t%s\t%s\t%s\n'%(rv2['province'],rv2['city'],rv2['town'],u'국외부재자',tmp_candidate,rv2['vote_list'][idx]))
        f_out[province_name].write('%s\t%s\t%s\t%s\t%s\t%s\n'%(rv3['province'],rv3['city'],rv3['town'],u'국내부재자',tmp_candidate,rv3['vote_list'][idx]))
        idx += 1
    
for tmp_f in f_out.values():
    tmp_f.close()
