#!/bin/bash

# Run this to get a listing of mac addresses from TCPdump
timeout $1 tcpdump -vvi $2 -qtel broadcast and port bootpc > tmp
awk '{if (length($1) == 17) print $1}' tmp | sort | uniq > mac.list
rm tmp
