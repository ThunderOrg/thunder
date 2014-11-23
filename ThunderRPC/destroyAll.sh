#!/bin/bash

domains=`virsh list | awk '{print $2}' | sed '1,2d' | sed '$d'`

for domain in $domains; do
   virsh destroy $domain
   virsh undefine $domain
   rm /srv/images/$domain.config
   rm /srv/images/$domain.img
done
