#!/bin/bash
DATE=`date +%Y-%m-%d`
FNAME=web/$DATE
EXT=tgz

if [[ -e $FNAME.$EXT ]]; then
    i=1
    NEWFNAME=$FNAME-$i
    while [[ -e $NEWFNAME.$EXT ]]; do
       i=$(($i + 1))
       NEWFNAME=$FNAME-$i 
    done
    FNAME=$NEWFNAME
fi

tar -czf $FNAME.$EXT -C / var/www
git add $FNAME.$EXT
