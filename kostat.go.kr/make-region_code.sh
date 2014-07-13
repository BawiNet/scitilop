#!/bin/bash

for LEVEL in 1 2 3 
do
  for RAW in $(ls geojson_raw/*$LEVEL.geojson.gz)
  do
    echo "$RAW -> region_code."$LEVEL".txt"
    ./geojson-list-code.py $RAW >> region_code.$LEVEL".txt"
  done
done
