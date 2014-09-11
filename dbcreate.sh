#!/bin/bash

# Preseed the database with the initial data for THUNDER

echo "Preseeding the MySQL database with values."
echo "------------------------------------------------"
echo "Password is 'thunder' by default."
if [ $# -ne 2 ];
then
   echo You must enter a NAS IP and MAC address!
   exit
fi
`sed "s/<IP>/$1/g;s/<MAC>/$2/g" preseed.sql | mysql -f -uroot -p`
echo "Done."
