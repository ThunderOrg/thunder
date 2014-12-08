import os
import platform
import libvirt

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

   nproc = open('/proc/cpuinfo', 'r')
   num_proc = 0
   for line in nproc:
      if (line[:9] == "processor"):
         num_proc += 1

   num_proc *= constants.get('default.vcoresPerCore')

   activeVCores = 0

   conn = libvirt.open() 
   for dom in conn.listAllDomains():
      activeVCores += int(dom.info()[3])
   conn.close()

   retVal = memtotal + ":" + memfree + ":" + oneMin + ":" + fiveMin + ":" \
                     + fifteenMin + ":" + str(num_proc) + ":" \
                     + str(activeVCores)

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
