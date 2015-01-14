#!/bin/bash
WWW_ROOT=/var/www/html
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

REV=`git rev-list --count HEAD`
cd $WWW_ROOT
echo $REV > rev
tar --exclude='./ubuntu' -czf $FNAME.$EXT ./* 
cd $WD

mv $WWW_ROOT/$FNAME.$EXT $WD/$FNAME.$EXT
git add $FNAME.$EXT
echo 'Done.';
