# -- coding: utf-8 --

import xlrd
import os
import sys

for filename in os.listdir('.'):
    if( not filename.endswith('.xls') ):
        continue

    wb = xlrd.open_workbook(filename, encoding_override='cp1252')
    wb.sheet_names()
    sh = wb.sheet_by_index(0)
    i = 0
    sys.stderr.write('Process %s (%d x %d)\n'%(filename,sh.ncols,sh.nrows))
    with open(filename+'.txt', "w") as my_file:
        while( i < sh.nrows ):
            out_str = '\t'.join(sh.row_values(i,1,18))
            my_file.write(out_str.encode('utf-8')+'\n')
            i += 1

