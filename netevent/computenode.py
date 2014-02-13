#!/usr/bin/env python3
from NetEvent import *
from subprocess import call
#import libvirt

def main():
   netEvent = NetEvent(0,'eth0','CLIENT','PRIMARY_COMPUTE','1')
   netEvent.registerEvent("INSTANTIATE", instantiate)
   netEvent.findPublisher()

def instantiate(params):
   # Instantiate a virtual machine
   vmName = params[0]
   #conn = libvirt.open("qemu:///system")
   #if (conn == None):
   #   return -1

   #try :
   #   vm = conn.lookupByName(vmName)
   #   vm.create()
   #except:
   #   return -1

   # Parse the MAC address from the virtual machine
   # connection and then use ARP to get the IP address
   return 1 #getIPAddr(vm)

main()
