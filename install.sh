#!/bin/bash

if [ $# -eq 0 ] || [ $# -gt 1 ] || ( [ "$1" != "head" ] && [ "$1" != "compute" ] );
then
   echo "Argument should be (head|compute)"
   exit
fi

if [ "$1" == "head" ];
then
   apt-get -y install apache2 mysql-server python3 python3-crypto python python-crypto cobbler php5
   ./restoreweb.sh
   ./dbcreate.sh      
else
   apt-get -y install apache2 python3 python3-crypto python python-crypto python-virt libvirt-bin libvirt-dev
fi
