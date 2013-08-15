# git clone this project
git clone https://github.com/stef/ec-experts-.git
cd ec-experts

# install required dependencies
# or if not on debian/ubuntu
# sudo pip install -r requirements.txt
apt-get install python-lxml python-dateutil

# create data directory
mkdir data

# run an update
./update.sh
