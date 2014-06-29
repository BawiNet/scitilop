#!/bin/bash
#ELECTION_TYPE="legislative"
#ELECTION_ID="20120411"
ELECTION_TYPE="presidential"
ELECTION_ID="20121219"

for CITY in $(cat city_code.txt | awk '{print $1}')
do
  echo $CITY
  OUT="voter.$ELECTION_TYPE.$ELECTION_ID.$CITY.tsv"
  echo "#Region	City	Town	VoteUnit	Population	VoterM	VoterF	RemoteM	RemoteF	House" > $OUT
  for HTML in $(ls $ELECTION_TYPE.raw/voter.$ELECTION_TYPE.$ELECTION_ID.$CITY.*)
  do
    echo $HTML
    ./parse-voter.py $HTML >> $OUT
  done
done
