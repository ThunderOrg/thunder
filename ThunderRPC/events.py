#!/usr/bin/env python3

'''
events.py
-----------------
Default events for metadata aggregation
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
import os
import platform
import libvirt
from networking import createMessage, parseMessage

'''
utilization(*params) ---
    Expected action:
        Determine the utilization of RAM and CPU

    Expected positional arguments:
        None

    Expected return value:
        Colon delimited string of data in the following form:
        "<memtotal>:<memfree>:<load1>:<load5>:<load15>:<#Cores>:<activeCores>"
        Where loadX denotes the average CPU load over X minutes
'''
def utilization(*params):
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

   nproc = open('/proc/cpuinfo', 'r')
   num_proc = 0
   for line in nproc:
      if (line[:9] == 'processor'):
         num_proc += 1

   num_proc *= constants.get('default.vcoresPerCore')

   activeVCores = 0

   conn = libvirt.open() 
   for dom in conn.listAllDomains():
      activeVCores += int(dom.info()[3])
   conn.close()

   retVal = [memtotal,memfree,oneMin,fiveMin,                                  \
             fifteenMin,str(num_proc),str(activeVCores)]

   return retVal

'''
sysInfo(*params) ---
    Expected action:
        Determine the operating system, kernel, and architecture
        of the machine

    Expected positional arguments:
        None

    Expected return value:
        A string containing the information in the following form:
        "<osName>:<kernel>:<architecture>"
'''
def sysInfo(*params):
   fullOsName = ''
   for i in platform.dist():
      fullOsName += i + ' '
   fullOsName = fullOsName[:-1]
   shortOsName = os.uname()[0]
   kernel = os.uname()[2]
   arch = os.uname()[4]

   retVal = [shortOsName, fullOsName, kernel, arch]
   return retVal
