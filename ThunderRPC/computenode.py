#!/usr/bin/env python3

# Compute Controller (Thor) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

from ThunderRPC import *
from subprocess import call

def main():
   client = ThunderRPC()
   client.registerEvent("INSTANTIATE", instantiate)
   client.findPublisher()

def instantiate(*params):
   tag = params[0]
   data = params[1]

   # Instantiate a virtual machine
   vmName = data[0]
   
   # Parse the MAC address from the virtual machine
   # connection and then use ARP to get the IP address
   return 1 #getIPAddr(vm)

main()
