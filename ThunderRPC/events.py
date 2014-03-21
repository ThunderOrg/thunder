import os
import platform

def utilization(*params):
   # extract the tag and data
   tag = params[0]
   data = params[1]

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

def sysInfo(*params):
   # extract the tag and data
   tag = params[0]
   data = params[1]

   fullOsName = ''
   for i in platform.dist():
      fullOsName += i + ' '
   fullOsName = fullOsName[:-1]
   shortOsName = os.uname()[0]
   kernel = os.uname()[2]
   arch = os.uname()[4]

   retVal = shortOsName + " (" + fullOsName + "):" + kernel + ":" + arch
   return retVal
