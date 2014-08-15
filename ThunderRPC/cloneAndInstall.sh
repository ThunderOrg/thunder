#!/bin/bash
conf="$2.iso"
virsh vol-clone --pool default $1 $2 &>/dev/null
cp /var/lib/libvirt/images/configuration.iso /var/lib/libvirt/images/$conf
virsh pool-refresh default &>/dev/null
virt-install -r 1024 -n $2 --vcpus=1 --autostart --noautoconsole --graphics vnc --memballoon virtio --boot hd --disk vol=default/$2,format=qcow2,bus=virtio --disk vol=default/$conf,bus=virtio &>/dev/null 
MAC=`virsh dumpxml $2 | grep 'mac address' | cut -d\' -f2`
IP=''
while [ -z "$IP" ]
do
   IP=`arp -n | grep $MAC | awk '{print $1}'`
done
echo $IP
