#!/bin/bash

#Configure a client (node) for deployment with cobbler

NAME=$1
PROFILE=$2
MAC=$3

cobbler system add --name=$NAME --profile=$PROFILE --mac=$MAC --netboot-enabled=Y
