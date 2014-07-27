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
            out_list = []
            for tmp in sh.row_values(i,1,sh.ncols):
                if( isinstance(tmp,int) or isinstance(tmp,float) ):
                    out_list.append( '%d'%tmp )
                else:
                    out_list.append(tmp)
            out_str = '\t'.join(out_list)
            my_file.write(out_str.encode('utf-8')+'\n')
            i += 1

