#!/bin/bash

# Preseed the database with the initial data for THUNDER

echo $#
echo "Preseeding the MySQL database with values."
echo "------------------------------------------------"
echo "Password is 'thunder' by default."
if [ $# -eq 2 ]
then
   sed "s/<IP>/$1/g" preseed.sql > tmp
   sed "s/<MAC>/$2/g" tmp > tmp
else
   echo You must enter a NAS IP and MAC address!
   exit
fi
mysql -f -uroot -p < tmp
rm tmp
echo "Done."
