#!/usr/bin/env python3
from NetEvent import *
import os
import platform

def main():
   netEvent = NetEvent()
   netEvent.registerEvent("STATUS", getStatus)
   netEvent.registerEvent("UTILIZATION", utilization)
   netEvent.registerEvent("SYSINFO", sysInfo)
   netEvent.registerEvent("INSTANTIATE", instantiate)
   netEvent.associateGroup("PRIMARY_COMPUTE")
   master = netEvent.findMaster()

def utilization(params):
   # Get memory utilization
   memInfo = open('/proc/meminfo','r')
   memtotal = memInfo.readline().split(':')[1].strip().split()[0]
   memfree = memInfo.readline().split(':')[1].strip().split()[0]
   memInfo.close()

   # Get CPU load averages
   loadAvg = open('/proc/loadavg', 'r')
   data = loadAvg.readline().split()
   loadAvg.close()
   oneMin = data[0]
   fiveMin = data[1]
   fifteenMin = data[2]

   retVal = memtotal + ":" + memfree + ":" + oneMin + ":" + fiveMin + ":" + fifteenMin
   return retVal

def sysInfo(params):

   fullOsName = ''
   for i in platform.dist():
      fullOsName += i + ' '
   fullOsName = fullOsName[:-1]
   shortOsName = os.uname()[0]
   kernel = os.uname()[2]
   arch = os.uname()[4]

   retVal = shortOsName + " (" + fullOsName + "):" + kernel + ":" + arch
   return retVal

def getStatus(params):
   # Read from the database the number of running instances
   print("---TODO: Return number of running vm instances---")
   return 1
   
def instantiate(params):
   # Instantiate a virtual machine
   print("---TODO: Invoke KVM or Xen to instantiate an image---")
   return 1

main()

