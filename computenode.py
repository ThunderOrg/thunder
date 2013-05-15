#!/usr/bin/env python3
from NetEvent import *
import os
import platform

def main():
   netEvent = NetEvent()
   netEvent.registerEvent("INSTANTIATE", instantiate)
   netEvent.associateGroup("PRIMARY_COMPUTE")
   netEvent.findController()

def instantiate(params):
   # Instantiate a virtual machine
   print("---TODO: Invoke KVM or Xen to instantiate an image---")
   return 1

main()
