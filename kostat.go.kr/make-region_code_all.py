#!/usr/bin/env python
import os
import sys

def read_code(filename):
    rv = dict()
    f = open(filename,'r')
    for line in f:
        tokens = line.strip().split()
        rv[tokens[0]] = tokens[1]
    f.close()
    return rv

code1 = read_code('region_code.1.txt')
code2 = read_code('region_code.2.txt')
code3 = read_code('region_code.3.txt')

f_out = open('region_code_all.txt','w')
for tmp_code3 in sorted(code3.keys()):
    tmp_code1 = tmp_code3[:2]
    tmp_code2 = tmp_code3[:5]
    f_out.write("%s\t%s\t%s\t%s\t%s\t%s\n"%(tmp_code1,tmp_code2,tmp_code3,code1[tmp_code1],code2[tmp_code2],code3[tmp_code3]))
f_out.close()
