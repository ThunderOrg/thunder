#!/bin/bash

# Preseed the database with the initial data for THUNDER

echo "Preseeding the MySQL database with values."
echo "------------------------------------------------"
echo "Password is 'thunder' by default."
mysql -uroot -p < preseed.sql
echo "Done."
