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

# get the MAC address of the desired networking interface
def getMAC(interface):
    p = subprocess.Popen(['/sbin/ifconfig', interface.strip()],                \
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ifconfig = p.communicate()[0]
    if (ifconfig):
        data = ifconfig.decode().split('\n')
        for item in data:
            itemArr = item.strip().split()
            found = False
            for field in itemArr:
                if (found):
                    return field.strip()
                # find the MAC address from the ifconfig output
                elif (field.lower() == 'hwaddr'):
                    found = True
    return None

# parse the local IP routing table for entries
def ipRouteList(self):
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
