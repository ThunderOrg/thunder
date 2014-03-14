#!/bin/bash

if [ $# -eq 0 ] || [ $# -gt 1 ] || ( [ "$1" != "head" ] && [ "$1" != "compute" ] );
then
   echo "Argument should be (head|compute)"
   exit
fi

if [ "$1" == "head" ];
then
   NASADDR=$1
   apt-get -y install apache2 mysql-server python3 python3-crypto python python-crypto cobbler php5 python3-setuptools
   easy_install3 pip
   pip install --allow-external mysql-connector-python mysql-connector-python
   ./restoreweb.sh
   ./dbcreate.sh $1 
else
   apt-get -y install apache2 python3 python3-crypto python python-crypto python-virt libvirt-bin libvirt-dev
fi
