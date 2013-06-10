#!/usr/bin/env python3
from NetEvent import *
from subprocess import call
#import libvirt

def main():
   netEvent = NetEvent()
   netEvent.registerEvent("INSTANTIATE", instantiate)
   netEvent.registerEvent("MOUNTSTORE", mountStore)
   netEvent.associateGroup("PRIMARY_COMPUTE")
   netEvent.findController()

def mountStore(params):
   username = params[0]
   password = params[1]
   address = params[2]
   store = params[3]
   call(["mount","-t cifs -o username=" + username + ",password="+ password + "//" + address + "/" + store + "/thunder_store"])
   return 1

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
