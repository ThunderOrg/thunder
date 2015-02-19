#!/usr/bin/env python3

'''
networking.py
-----------------
Support some networking operations for THUNDER
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
import subprocess
import shutil
import fileinput
from time import time, sleep

'''
getIP(interface) ---
    Expected action:
        Finds the IP address of the given interface

    Expected positional arguments:
        interface - The name of an interface

    Expected return value:
        The IP address if interface is valid
        '127.0.0.1' otherwise
'''
def getIP(interface):
    p = subprocess.Popen(['/sbin/ifconfig', interface.strip()],                \
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ifconfig = p.communicate()[0]
    if (ifconfig):
        data = ifconfig.decode().split('\n')
        for item in data:
            item = item.strip()
            # find the IP address from the ifconfig output
            if (item.startswith('inet ')):
                if (platform.system() == 'Darwin'):
                    return item.split(' ')[1]
                else:
                    return item.split(':')[1].split()[0]
    return '127.0.0.1'

'''
getInterfaceFromIP(ip) ---
    Expected action:
        Finds the interface name given a particular IP address

    Expected positional arguments:
        ip - a valid IP address assigned to this machine

    Expected return value:
        The interface name, or the empty string if none found
'''
def getInterfaceFromIP(ip):
    cmd = "ifconfig | grep -B1 \"inet addr:{0:s}\" | awk '{print $1}' | " +    \
          "head -n1".format(ip)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ifconfig = p.communicate()[0]
    return ifconfig

'''
getMAC(node) ---
    Expected action:
        Converts the hex value of the node name to proper MAC

    Expected positional arguments:
        node - Hex value returned from getNode()

    Expected return value:
        The proper MAC address of the node
'''
def getMAC(node):
    hexMac = hex(node)
    mac = ''
    for i in range(2,len(hexMac),2):
       mac+=hexMac[i]+hexMac[i+1]+'-'
    return mac[:-1]

# parse the local IP routing table for entries
def ipRouteList():
    addresses = []
    p = subprocess.Popen(['/sbin/ip', 'route', 'list'], stdout=subprocess.PIPE,\
                         stderr=subprocess.PIPE)
    iptable = p.communicate()[0]
    if (iptable):
        data = iptable.decode().split('\n')
        for line in data:
            lineArr = line.split()
            for i in range(0, len(lineArr), 1):
                if (lineArr[i].strip().lower == 'src'):
                    addresses += [lineArr[i+1]]
    return addresses

def getDHCPRenewTime(mac):
    result = None
    fp = open(constants.get('default.dhcpdLeases'), 'r')
    entries = fp.readlines()
    fp.close()
    for i in range(len(entries)-1, -1, -1):
        line = entries[i]
        if mac.replace('-', ':') in line:
           foundTime = False
           while (not foundTime and i > -1):
              i -= 1
              line = entries[i]
              if 'starts' in line:
                  foundTime = True
           if foundTime:
              result = line.split()[-1]
              break
    return result

def getIPFromDHCP(mac):
   result = None
   done = False
   while (not done):
      fp = open(constants.get('default.dhcpdLeases'), 'r')
      entries = fp.readlines()
      fp.close() 
      for i in range(len(entries)-1, -1, -1):
         line = entries[i]
         if mac.replace('-', ':') in line:
            foundIP = False
            while (not foundIP and i > -1):
               i -= 1
               line = entries[i]
               if 'lease' in line:
                  foundIP = True
            if foundIP:
               result = line.split()[1]
               done = True
               break
      sleep(5)
   return result

def getIPFromARP(mac):
   mac = mac.replace('-', ':')
   # Remove any previous entry for this mac address
   cmd = "/usr/sbin/arp -d `arp -an | grep " + mac + " | awk '{print $2}' | tr -d '()'`"
   subprocess.call(cmd + " > /dev/null 2>&1", shell=True)
   cmd = "./iplookup.sh"
   out = ""
   start_time = int(round(time()*1000))
   cur_time = start_time
   max_time = constants.get('default.maxIPWait')

   while (out == "" and start_time - cur_time < max_time):
      p = subprocess.Popen([cmd, mac], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = p.communicate()
      out = out.decode().strip()
      cur_time = int(round(time() * 1000))

   return out

def generatePreseed(ip):
   wwwDir = constants.get('default.wwwdir')
   template = wwwDir  + '/preseed_template.cfg'
   template_bare = wwwDir  + '/preseed_bare_template.cfg'
   shutil.copyfile(template, wwwDir + '/preseed_compute.cfg')
   shutil.copyfile(template, wwwDir + '/preseed_storage.cfg')
   shutil.copyfile(template, wwwDir + '/preseed_controller.cfg')
   shutil.copyfile(template_bare, wwwDir + '/preseed_bare.cfg')
   configs = ['compute', 'storage', 'controller', 'bare']
   for config in configs:
      for line in fileinput.input(wwwDir + '/preseed_' + config + '.cfg', inplace=True):
         if '<ROLE>' in line or '<SERVER_IP>' in line:
            print(line.replace('<ROLE>', config).replace('<SERVER_IP>', ip), end='')
         else:
            print(line, end='')
   shutil.chown(wwwDir + '/preseed_compute.cfg', user='thunder', group='thunder')
   shutil.chown(wwwDir + '/preseed_storage.cfg', user='thunder', group='thunder')
   shutil.chown(wwwDir + '/preseed_bare.cfg', user='thunder', group='thunder')
   shutil.chown(wwwDir + '/preseed_controller.cfg', user='thunder', group='thunder')

