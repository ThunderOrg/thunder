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

# create a storage pool for this domain
virsh pool-define-as $domain dir - - - - $dest/$domain
virsh pool-build $domain
virsh pool-start $domain

mv $archive $domain/
cd $domain
tar xf $archive
rm $archive

# if there is an overlay image then copy it, otherwise use the base image
if [[ -n "$overlay" ]]; then
   imageName=$overlay
else
   imageName=$disk
fi

cd ..

virsh pool-refresh $domain

virt-install -r $ram -n $domain --vcpus=$vcpus --hvm --autostart --noautoconsole --vnc --force --accelerate --memballoon virtio --boot hd --disk vol=$domain/$imageName,format=qcow2,bus=virtio --disk vol=$domain/$config,bus=virtio
sleep 1
MAC=`virsh dumpxml $domain | grep 'mac address' | cut -d\' -f2 | tr -d ' '`
} > /dev/null 2>&1

echo $MAC
