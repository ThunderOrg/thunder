import subprocess
import shutil
import fileinput
from time import sleep

# get the IP of the desired networking interface
def getIP(interface):
    if (interface == 'ALL'):
        return '0.0.0.0'

    p = subprocess.Popen(['/sbin/ifconfig', interface.strip()],                \
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ifconfig = p.communicate()[0]
    if (ifconfig):
        data = ifconfig.decode().split('\n')
        for item in data:
            item = item.strip()
            # find the IP address from the ifconfig output
            if (item.startswith('inet ')):
                print(item)
                if (platform.system() == 'Darwin'):
                    return item.split(' ')[1]
                else:
                    return item.split(':')[1].split()[0]
    return '127.0.0.1'

def getInterfaceFromIP(ip):
    cmd = "ifconfig | grep -B1 \"inet addr:{0:s}\" | awk '{print $1}' | head -n1".format(ip)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ifconfig = p.communicate()[0]
    return ifconfig

# get the MAC address of the desired networking interface
def getMAC(node):
    hexMac = hex(node)
    mac = ""
    for i in range(2,len(hexMac),2):
       mac+=hexMac[i]+hexMac[i+1]+"-"
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
    fp = open(constants.get("default.dhcpdLeases"), "r")
    entries = fp.readlines()
    fp.close()
    for i in range(len(entries)-1, -1, -1):
        line = entries[i]
        if mac.replace('-', ':') in line:
           foundTime = False
           while (not foundTime and i > -1):
              i -= 1
              line = entries[i]
              if "starts" in line:
                  foundTime = True
           if foundTime:
              result = line.split()[-1]
              break
    return result

def getIPFromDHCP(mac):
   result = None
   done = False
   while (not done):
      fp = open(constants.get("default.dhcpdLeases"), "r")
      entries = fp.readlines()
      fp.close() 
      for i in range(len(entries)-1, -1, -1):
         line = entries[i]
         if mac.replace('-', ':') in line:
            foundIP = False
            while (not foundIP and i > -1):
               i -= 1
               line = entries[i]
               if "lease" in line:
                  foundIP = True
            if foundIP:
               result = line.split()[1]
               done = True
               break
      sleep(10)
   return result

def generatePreseed(ip):
   wwwDir = constants.get("default.wwwdir")
   template = wwwDir  + "/preseed_template.cfg"
   template_bare = wwwDir  + "/preseed_bare_template.cfg"
   shutil.copyfile(template, wwwDir + "/preseed_compute.cfg")
   shutil.copyfile(template, wwwDir + "/preseed_storage.cfg")
   shutil.copyfile(template, wwwDir + "/preseed_controller.cfg")
   shutil.copyfile(template_bare, wwwDir + "/preseed_bare.cfg")
   configs = ["compute", "storage", "controller", "bare"]
   for config in configs:
      for line in fileinput.input(wwwDir + "/preseed_" + config + ".cfg", inplace=True):
         if "<ROLE>" in line or "<SERVER_IP>" in line:
            print(line.replace("<ROLE>", config).replace("<SERVER_IP>", ip), end="")
         else:
            print(line, end="")
