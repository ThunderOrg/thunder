#!/bin/bash
{
domains=`virsh pool-list --all | awk '{print $1}' | sed '1,2d' | sed '$d'`

for domain in $domains; do
   virsh destroy $domain
   virsh undefine $domain
   vols=`virsh vol-list $domain | awk '{print $1}' | sed '1,2d' | sed '$d'`
   for vol in $vols; do
      virsh vol-delete $vol --pool $domain
   done
   virsh pool-destroy $domain
   virsh pool-delete $domain
   virsh pool-undefine $domain
done
} > /dev/null 2>&1

echo $domains
