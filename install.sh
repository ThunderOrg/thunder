#!/bin/bash

INTERFACE="eth0"
BRIDGE="br0"

if [ $# -eq 1 ];
then
   INTERFACE="$1"
fi

apt-get -y update
apt-get -y install virtinst libvirt-bin libvirt-dev bridge-utils

virsh iface-bridge $INTERFACE $BRIDGE
virsh pool-destroy default
virsh pool-undefine default
virsh pool-define-as --name default --type dir --target /var/lib/libvirt/images
virsh pool-autostart default
virsh pool-build default
virsh pool-start default

IP=`ifconfig $BRIDGE | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'`
MAC=`ifconfig $BRIDGE | grep 'HWaddr ' | awk '{ print $5}'`

debconf-set-selections <<< 'mysql-server mysql-server/root_password password thunder'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password thunder'

apt-get -y install build-essential python3 python3-dev apache2 mysql-server python3-crypto php5 python3-setuptools samba git libapache2-mod-php5 pyp5-mysql php5-memcache php5-memcached memcached

easy_install3 pip
pip3 install PyMySQL
pip3 install libvirt-python

mkdir -p /srv/thunder 
cd /srv
git clone https://github.com/paranoidgabe/pysmb.git
cd pysmb
python3 setup.py install
cd ..
git clone https://github.com/paranoidgabe/thunder.git
cd thunder
mkdir -p /var/www/html
./restoreweb.sh

`sed -i '/bind-address/ s/^#*/#/' /etc/mysql/my.cnf`

./dbcreate.sh $IP $MAC <<< "thunder\n"
#brctl addbr br0
#brctl addif br0 $INTERFACE
cp upstart/* /etc/init/
cat storage.conf >> /etc/samba/smb.conf
mkdir -p /srv/storage/images/ubuntu
cd /srv/storage/images/ubuntu
wget 130.160.68.90/config.img
wget 130.160.68.90/disk.img
service thunderserver start
service thundercompute start
