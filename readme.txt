# you can automatically install and run ec-experts if you are running
# debian or ubuntu by issuing the following command
# wget -O - https://raw.github.com/stef/ec-experts/master/readme.txt | sh -

# git clone this project
git clone https://github.com/stef/ec-experts.git
cd ec-experts

# install required dependencies
# or if not on debian/ubuntu
# sudo pip install -r requirements.txt
sudo apt-get install python-lxml python-dateutil

# create data directory
mkdir data

# run an update
./update.sh

# update.sh performs the following steps:
# (you can and should use the command below to achieve manual improvements 
# when deduplicating)

# 1. you download the newest expert register dump from:
# "http://ec.europa.eu/transparency/regexpert/view/transparency/openXML.cfm?file=RegExp_xml_{today}.xml"
# where you have to replace {today} with the date in the following format:
# YYYYMMDD

# 2. extract register from xml dump to json
# this is needed for all the following steps, but only once
# after downloading the dump in step 1.
# python extract.py data/regexp_{today}.xml >data/regexp_{today}.json
# again replace {today} with the date in the format from step 1.

# 3. transform and dump expert register
# this step deduplicates the names from the intermediary format in step 2.
# using the contents of dedup.txt found in this directory.
# you can add more deduplication blocks or edit the existing ones to
# achieve better results.
# this step generates a csv file called data/entities-{today}.csv
# which you can use for further datamining.
# python experts.py data/regexp_{today}.json dedup.txt >data/entities-{today}.csv
# don't forget to replace {today} with YYYYMMDD

# 4. optionally (update.sh does this automatically) find new
# candidates for dedup expert and rep names.
# python dedup.py data/entities-{today}.csv org_name >data/dedup-{today}.txt
# notice the "org_name" in above line, this command searches for
# possible duplicate names in all the organisation names and outputs
# these into data/dedup-${today}.txt

# alternatively you can run a similar command for the names of the
# experts: 
# python dedup.py data/entities-${today}.csv name >>data/dedup-${today}.txt
# notice the >> which appends and not overwrites the results for the
# organizations in the previous example. Also notable i the change
# from "org_name" to "name", which is neccessary for selecting the
# names of the experts.

# That's about it. You should perform steps 3. and 4. iteratively,
# while editing dedup.txt and merging dedup candidate blocks from
# data/dedup-${today}.txt into it, until you have a
# data/entities-{today}.csv file that is clean enough for you.

# you can redo also steps 1. and 2. daily, to regenerate the csv based
# on the newest data from the commission.
