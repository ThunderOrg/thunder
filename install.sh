#!/bin/bash

INTERFACE="eth0"

if [ $# -eq 1 ];
then
   INTERFACE="$1"
fi

IP=`ifconfig $INTERFACE | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'`
MAC=`ifconfig $INTERFACE | grep 'HWaddr ' | awk '{ print $5}'`

apt-get -y install apache2 mysql-server python3 python3-crypto php5 python3-setuptools bridge-utils samba
easy_install3 pip git
pip install PyMySQL
mkdir -p /srv/thunder
cd /srv/thunder
git clone https://github.com/paranoidgabe/thunder.git
./restoreweb.sh
./dbcreate.sh $IP $MAC
brctl addbr br0
brctl addif br0 $INTERFACE
cp upstart/* /etc/init.d/
cat storage.conf >> /etc/samba/smb.conf
mkdir -p /srv/storage/
service thunderserver start
service thundercompute start
