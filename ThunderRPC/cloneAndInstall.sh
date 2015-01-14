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
mkdir _$domain
mv $archive ./_$domain/
cd _$domain
tar xf $archive
mv $disk ../$domain.base
mv $config ../$domain.config

# if there is an overlay image then copy it, otherwise use the base image
if [[ -n "$overlay" ]]; then
   mv $overlay ../$domain.overlay
   imageName=$domain.overlay
else
   imageName=$domain.base
fi

cd ..
rm -rf _$domain

virsh pool-refresh default

virt-install -r $ram -n $domain --vcpus=$vcpus --hvm --autostart --noautoconsole --vnc --force --accelerate --memballoon virtio --boot hd --disk vol=default/$imageName,format=qcow2,bus=virtio --disk vol=default/$domain.config,bus=virtio

} > /dev/null 2>&1

MAC=`virsh dumpxml $domain | grep 'mac address' | cut -d\' -f2`
echo $MAC
