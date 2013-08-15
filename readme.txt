# you can automatically install and run ec-experts by issuing the following
# command
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
