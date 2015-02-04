#!/bin/bash

{
IP=`arp -an | grep $1 | awk '{print $2}' | tr -d '()'`
} > /dev/null 2>&1
echo $IP
