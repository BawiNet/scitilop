#!/usr/bin/env python
import os
import sys
import gzip
import json

filename_geojson = sys.argv[1]
output_name = sys.argv[2]

svg_width = 600
svg_height = 600
svg_margin_x = 20
svg_margin_y = 20

## default color code for region
color_region = {u'11':'red', u'21':'blue',u'22':'blue', u'23':'blue', u'24':'blue', u'25':'blue', u'26':'blue',\
                u'29':'cyan', u'31':'green', u'32':'green', u'33':'green', u'34':'green', u'35':'green',\
                u'36':'green', u'37':'green', u'38':'green', u'39':'green'}

f_geojson = open(filename_geojson,'r')
if( filename_geojson.endswith('.gz') ):
    f_geojson = gzip.open(filename_geojson,'rb')
tmp_geojson = json.load(f_geojson)
f_geojson.close()

min_x, min_y, max_x, max_y = (-1,-1,-1,-1)
def update_min_max(tmp_x, tmp_y):
    global min_x, min_y, max_x, max_y
    if( min_x < 0 or min_x > tmp_x ):
        min_x = tmp_x
    if( max_x < 0 or max_x < tmp_x ):
        max_x = tmp_x
    if( min_y < 0 or min_y > tmp_y ):
        min_y = tmp_y
    if( max_y < 0 or max_y < tmp_y ):
        max_y = tmp_y

for tmp in tmp_geojson['features']:
    for tmp_coord_list in tmp['geometry']['coordinates']:
        if( tmp['geometry']['type'] == 'MultiPolygon' ):
            for tmp_embed_coord_list in tmp_coord_list:
                for tmp_x, tmp_y in tmp_embed_coord_list:
                    update_min_max(tmp_x, tmp_y)
        else:
            for tmp_x, tmp_y in tmp_coord_list:
                update_min_max(tmp_x, tmp_y)

scale_x = (svg_width - svg_margin_x*2) * 1.0 / (max_x - min_x)
scale_y = (svg_height - svg_margin_y*2) * 1.0 / (max_y - min_y)
scale_min = min(scale_x, scale_y)

svg_header = """\
<svg version="1.1"
    baseProfile="full"
    width="%d" height="%d"
    xmlns="http://www.w3.org/2000/svg">
"""%(svg_width, svg_height)

#svg_polygon = '<polygon points="%s" style="fill:none;stroke:purple;stroke-width:1" />'
svg_polygon = '<polygon points="%s" class="region%s" />'
svg_footer = "</svg>"

f_svg = open('%s.svg'%output_name,'w')
filename_css = '%s.css'%output_name
f_css = open(filename_css,'w')

f_svg.write('<?xml version="1.0" standalone="no"?>\n')
f_svg.write('<?xml-stylesheet type="text/css" href="%s" ?>\n'%(filename_css))
f_svg.write(svg_header+"\n")
for tmp in tmp_geojson['features']:
    if( tmp['properties'].has_key('Name') ):
        tmp_code = tmp['properties']['Name']
    elif( tmp['properties'].has_key('admcode') ):
        tmp_code = tmp['properties']['admcode']
    
    if( tmp['properties'].has_key('Description') ):
        tmp_unit_name = tmp['properties']['Description']
    elif( tmp['properties'].has_key('admname') ):
        tmp_unit_name = tmp['properties']['admname']

    tmp_type = tmp['geometry']['type']
    f_svg.write('<!-- '+ tmp_unit_name.encode('utf-8') +'('+ tmp_code.encode('utf-8') +') -->\n')
    f_css.write('/* '+ tmp_unit_name.encode('utf-8') +'('+ tmp_code.encode('utf-8') +') */\n')
    f_css.write('polygon.region%s {fill:%s, stroke-width:1, stroke-color:white }\n'%(tmp_code, color_region[tmp_code]))

    if( tmp_type == 'Polygon' ):
        tmp_coord = ' '.join(['%f,%f'%(svg_margin_x+(x-min_x)*scale_x,svg_height-(y-min_y)*scale_y-svg_margin_y) for x,y in tmp['geometry']['coordinates'][0]])
        f_svg.write(svg_polygon%(tmp_coord,tmp_code)+'\n')

    elif( tmp_type == 'MultiPolygon' ):
        for tmp_coord_list in tmp['geometry']['coordinates']:
            if( tmp['geometry']['type'] == 'MultiPolygon' ):
                for tmp_embed_coord_list in tmp_coord_list:
                    tmp_coord = ' '.join(['%f,%f'%(svg_margin_x+(x-min_x)*scale_x,svg_height-(y-min_y)*scale_y-svg_margin_y) for x,y in tmp_embed_coord_list])
                    f_svg.write(svg_polygon%(tmp_coord,tmp_code)+'\n')

    #print ' '.join(['%f'%x for x in tmp['geometry']['coordinates'][0][0]])
    #print tmp_coord
f_svg.write(svg_footer+'\n')
f_svg.close()
f_css.close()
