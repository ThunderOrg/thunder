#!/bin/bash
virsh destroy $1
virsh undefine $1
virsh pool-destroy $1
virsh pool-undefine $1
rm -r /srv/images/$1
