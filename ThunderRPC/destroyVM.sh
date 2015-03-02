#!/bin/bash
virsh destroy $1
virsh undefine $1
vols=`virsh vol-list $1 | awk '{print $1}' | sed '1,2d' | sed '$d'`
for vol in $vols; do
      virsh vol-delete $vol --pool $domain
done
virsh pool-destroy $1
virsh pool-delete $1
virsh pool-undefine $1
