#!/bin/bash

# Preseed the database with the initial data for THUNDER

echo $#
echo "Preseeding the MySQL database with values."
echo "------------------------------------------------"
echo "Password is 'thunder' by default."
if [ $# -eq 1 ]
then
   sed "s/<IP>/$1/g" preseed.sql > tmp
else
   echo You must enter a NAS IP address!
   exit
fi
mysql -f -uroot -p < tmp
rm tmp
echo "Done."
