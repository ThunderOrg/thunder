#!/bin/bash

# Run this to get a listing of mac addresses from TCPdump
timeout 15 tcpdump -i eth0 -qtel broadcast and port bootpc > tmp
awk '{if (length($1) == 17) print $1}' tmp | sort | uniq > mac.list
rm tmp
