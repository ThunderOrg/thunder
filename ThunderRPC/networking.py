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
import json
from time import time, sleep

def createMessage(**kwargs):
    return json.dumps(kwargs).encode('UTF8')

def parseMessage(msg):
    if (type(msg) == type(bytes())):
       return json.loads(msg.decode('UTF8'))
    else:
       return json.loads(msg)

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

