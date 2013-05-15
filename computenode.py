#!/usr/bin/env python3
from NetEvent import *
import libvirt

def main():
   netEvent = NetEvent()
   netEvent.registerEvent("INSTANTIATE", instantiate)
   netEvent.associateGroup("PRIMARY_COMPUTE")
   netEvent.findController()

def instantiate(params):
   # Instantiate a virtual machine
   vmName = params[0]
   conn = libvirt.open("qemu:///system")
   if (conn == None):
      return −1

   try :
      vm = conn.lookupByName(vmName)
      vm.create()
   except:
      return −1

   # Parse the MAC address from the virtual machine
   # connection and then use ARP to get the IP address
   return 1#getIPAddr(vm)

main()
