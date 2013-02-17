#!/usr/bin/env python3
from NetEvent import *

def main():
   netEvent = NetEvent()
   netEvent.registerEvent("STATUS", getStatus)
   netEvent.registerEvent("INSTANTIATE", instantiate)
   netEvent.associateGroup("PRIMARY_COMPUTE")
   master = netEvent.findMaster()

def getStatus(params):
   # Read from the database the number of running instances
   print("---TODO: Return number of running vm instances---")
   return 1
   
def instantiate(params):
   # Instantiate a virtual machine
   print("---TODO: Invoke KVM or Xen to instantiate an image---")
   return 1

main()

