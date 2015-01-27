#!/bin/bash
{
domains=`virsh list | awk '{print $2}' | sed '1,2d' | sed '$d'`

for domain in $domains; do
   virsh destroy $domain
   virsh undefine $domain
   virsh pool-destroy $domain 
   virsh pool-undefine $domain 
   rm -r /srv/images/$domain
   rm -r /srv/images/$domain
done
} > /dev/null 2>&1

echo domains
