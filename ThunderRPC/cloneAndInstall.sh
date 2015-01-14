#!/bin/bash

archive=$1
domain=$2
disk=$3
overlay=$4
config=$5
ram=$6
vcpus=$7
dest=$8

{
cd $dest
mkdir $domain
mv $archive ./$domain/
cd $domain
tar xf $archive

# if there is an overlay image then copy it, otherwise use the base image
if [[ -n "$overlay" ]]; then
   imageName=$domain.overlay
else
   imageName=$domain.base
fi

cd ..

virsh pool-refresh default

virt-install -r $ram -n $domain --vcpus=$vcpus --hvm --autostart --noautoconsole --vnc --force --accelerate --memballoon virtio --boot hd --disk vol=default/$domain/$imageName,format=qcow2,bus=virtio --disk vol=default/$domain/$config,bus=virtio

} > /dev/null 2>&1

MAC=`virsh dumpxml $domain | grep 'mac address' | cut -d\' -f2`
echo $MAC
