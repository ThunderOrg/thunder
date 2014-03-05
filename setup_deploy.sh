#!/bin/bash

#Setup the thunder image and kickstart seed with cobbler

NAME=ubuntu-server
ISO=$NAME.iso
wget -O $ISO http://releases.ubuntu.com/12.04.4/ubuntu-12.04.4-server-amd64.iso
mount -o loop $ISO /mnt
cobbler import --name=$NAME --path=/mnt --breed=ubuntu
umount /mnt
cobbler profile edit --name=$NAME --kickstart=thunder.seed --kopts="priority=critical locale=en_US"
