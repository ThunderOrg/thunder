#!/bin/bash
WWW_ROOT=/var/www
WD=$(pwd)/web
DATE=`date +%Y-%m-%d`
FNAME=$DATE
EXT=tgz

echo 'Backing up web...';

if [[ -e $WD/$FNAME.$EXT ]]; then
    i=1
    NEWFNAME=$FNAME-$i
    while [[ -e $WD/$NEWFNAME.$EXT ]]; do
       i=$(($i + 1))
       NEWFNAME=$FNAME-$i 
    done
    FNAME=$NEWFNAME
fi

cd $WWW_ROOT
tar -czf $FNAME.$EXT ./*
cd $WD

mv $WWW_ROOT/$FNAME.$EXT $WD/$FNAME.$EXT
git add $FNAME.$EXT
echo 'Done.';
