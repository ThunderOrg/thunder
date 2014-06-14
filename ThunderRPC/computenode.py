#!/usr/bin/env python3

# Compute Controller (Thor) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

from thunder import *
from subprocess import call
import uuid

def main():
   client = ThunderRPC()
   client.registerEvent("INSTANTIATE", instantiate)
   client.findPublisher()

def instantiate(*params):
   tag = params[0]
   data = params[1]
    
   if (len(data) < 2):
      return "You must supply the virtual machine name and where it is located!"

   # get the specifics from the data
   vmname = data[0]
   location = data[1]

   # create an entry in the database for this request.
   # it will contain the IP address of the machine once it has started.
   id = uuid.uuid1()

   # call virt.py with vmname and location

   return id #getIPAddr(vm)

main()
