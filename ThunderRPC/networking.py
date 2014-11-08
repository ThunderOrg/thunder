import subprocess

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
       mac+=hexMac[i]+hexMac[i+1]+":"
    print(mac[:-1])
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
