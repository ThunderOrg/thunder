#!/bin/bash
{
virsh pool-refresh default
virt-install -r 1024 -n $3 --vcpus=1 --hvm --autostart --noautoconsole --vnc --force --accelerate --memballoon virtio --boot hd --disk vol=default/$1,format=qcow2,bus=virtio --disk vol=default/$2,bus=virtio
} > /dev/null 2>&1
MAC=`virsh dumpxml $3 | grep 'mac address' | cut -d\' -f2`
echo $MAC
