#!/usr/bin/env python3
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
