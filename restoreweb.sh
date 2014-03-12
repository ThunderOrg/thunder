#!/bin/bash

# Get a listing of correctly named backups
DIR="web"
cd $DIR
FILES=$(ls -d [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*.tgz)
cd ..

SORTED_FILES=($(for FILE in $FILES; do echo $FILE; done | sort))
SIZE=${#SORTED_FILES[@]}
LATEST=${SORTED_FILES[$SIZE-1]}

echo "Removing old www contents"
rm -r /var/www/*

echo "Restoring backup: $LATEST"
tar -xzf $DIR/$LATEST -C /var/www/
