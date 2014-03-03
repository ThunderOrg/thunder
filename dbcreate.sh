#!/bin/bash
echo "Preseeding the MySQL database with values."
echo "------------------------------------------------"
echo "Password is 'thunder' by default."
mysql -uroot -p < preseed.sql
echo "Done."
