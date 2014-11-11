#!/bin/bash

# Preseed the database with the initial data for THUNDER

echo "Preseeding the MySQL database with values."
echo "------------------------------------------------"
`cat preseed.sql | mysql -f -uroot -pthunder`
echo "Done."
