#!/bin/sh

echo "have you updated the dedup file?"

today=$(date +%Y%m%d)

curl -L "http://ec.europa.eu/transparency/regexpert/view/transparency/openXML.cfm?file=RegExp_xml_${today}.xml" -o "data/regexp_${today}.xml"

# extract register from xml dump to json
python extract.py data/regexp_${today}.xml >data/regexp_${today}.json

# transform and dump expert register
echo "generating new csv"
python experts.py data/regexp_${today}.json entities-201308237_MASTER_PS.csv dedup.txt >data/entities-${today}.csv

# dedup expert and rep names
echo "searching for dedup candidates"
python dedup.py data/entities-${today}.csv org_name >data/dedup-${today}.txt
echo >>data/dedup-${today}.txt
python dedup.py data/entities-${today}.csv name >>data/dedup-${today}.txt

echo "csv file" data/entities-${today}.csv
echo "dedup candidates" data/dedup-${today}.txt
