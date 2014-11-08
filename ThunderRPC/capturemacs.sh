#!/bin/bash

nmap -PR -sP 10.10.0.0/16 > /dev/null 2>&1

awk ' { out = ""} \
      { $1=="lease"||$1=="client-hostname" ? out=" " $2: out=out } \
      { $1=="binding"||$1=="hardware" ? out= " " $3: out=out } \
      { $1=="ends"? out=" " $3 " " $4: out=out } \
      { $1=="}"? out="\n": out=out } \
      { printf out," " }' /var/lib/dhcp/dhcpd.leases \
  | grep active \
  | sed -e s/'[{};" ]'/\ /g  \
  | awk '{ printf "%-17s\n", $5}' > tmp.lst

arp -a \
  | sed -e s/\\..*\(/\ / -e s/\)// \
  | awk '{ printf "%-17s\n", $4}' >> tmp.lst

cat tmp.lst \
  | grep -Eo '^([0-9a-fA-F][0-9a-fA-F]:){5}([0-9a-fA-F][0-9a-fA-F])$' \
  | sort -u
