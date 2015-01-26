#!/usr/bin/env python3

'''
rpc.py
-----------------
Remote procedure call handler for THUNDER
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
import auth, socket, socketserver, threading, libvirt, load_balancer 
import subprocess, shutil, fileinput, networking, threading, os, urllib.request
from websocket import *
from mysql_support import *
from time import sleep
from enum import Enum

class LBMode(Enum):
   RAIN=0
   ROUNDROBIN=1
   CONSOLIDATE=2
   RANDOM=3

'''
ThunderRPCServer(socketserver.ThreadingMixIn, socketserver.TCPServer) ---
Dummy class used to ensure per-request threading
'''
class ThunderRPCServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

'''
RequestHandler(socketserver.BaseRequestHandler) ---
Each request should be given an independent thread, each handled by
the RequestHandler class
'''
class RequestHandler(socketserver.BaseRequestHandler):
    '''
    setup() ---
        Expected action:
           Sets up the socket for blocking communication on default
           also enables background process (daemon) mode for threads.

        Expected positional arguments:
           Nonde

        Expected return value:
           None
    '''
    def setup(self):
        self.daemon_threads = True
        self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY, True)
        self.request.setblocking(1)
        self.lbMode = LBMode['RAIN']
        return
    '''
    handle() ---
        Expected action:
           Reads data from the socket server, determines whether it
           is a raw message or if it is wrapped in a HYBI websocket
           frame.  Calls the appropriate handler to process the data.

        Expected positional arguments:
           Nonde

        Expected return value:
           None
    '''
    def handle(self):
        self.container = self.server._ThunderRPCInstance
        self.data = self.request.recv(4096)
        websock = websocket(self.request)
        decodedData = ''
        ws = False

        # Check to see if the data is coming over a websocket connection
        # (cloud interface)
        if (websock.isHandshakePending(self.data)):
            handshake = websock.handshake(self.data.decode())
            self.request.sendall(handshake)
            d = self.request.recv(2)
            decodedData = websock.decode(d).strip()
            ws = True
        # Else, it could be coming from a peer (cloud server)
        else:
            decodedData = self.data.decode('UTF8').strip()

        # if there is data waiting to be processed then process it!
        if (decodedData != ''):
            if (ws):
                self.processWebsocketRequest(decodedData.split(), websock)
            else:
                self.processTraditionalRequest(decodedData.split())

        self.request.close()
        return

    '''
    processWebsocketRequest(data, websock) ---
        Expected action:
           Process incoming messages from the web interface
           relay these messages to other nodes if need
           be and return a response to the caller

        Expected positional arguments:
           data - the raw message after websocket headers have been removed
           websock - the websock object used to re-encode responses

        Expected return value:
           None
    '''
    def processWebsocketRequest(self, data, websock):
        clients = self.container.clients
        # check if the client is requesting data from a group
        if (data[0] == 'EXECGROUP'):
            group = data[1]
            res = self.container.publishToGroup(group, data[2])
            if (res != None):
                self.request.sendall(websock.encode(Opcode.text, res))

        # check if the client is requesting data from a node
        elif (data[0] == 'EXECNODE'):
            node = (data[1], int(data[2]))
            res = self.container.publishToHost(node, data[3])
            if (res != None):
                self.request.sendall(websock.encode(Opcode.text, res))

        # check if the client is requesting a list of clusters available
        elif (data[0] == 'GROUPNAMES'):
            self.request.sendall(websock.encode(Opcode.text,                   \
                                 self.container.getClusterList()))

        # check if the client is requesting a list of nodes in a particular
        # cluster
        elif (data[0] == 'NODESINGROUP'):
            clients = self.container.getClientList(data[1])
            self.request.sendall(websock.encode(Opcode.text, clients))

        # check if the client is requesting the server to poll for mac
        # addresses, used for deployment
        elif (data[0] == 'POLLMACS'):
            p = subprocess.Popen('./capturemacs.sh', stdout=subprocess.PIPE,   \
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            macs = out.decode().rstrip().split('\n')
            result = ''
            for mac in macs:
                if (not mac.startswith(constants.get('default.vmMACPrefix'))):
                    result+=mac.strip() + ';'
            self.request.sendall(websock.encode(Opcode.text, result[:-1]))

        elif (data[0] == 'INSTANTIATE'):
            self.container.cleanupClients()
            nodes = clients.get('COMPUTE')
            # Message style:
            # INSTANTIATE <VM_NAME> <USER_NAME>
            message = data[0] + ' ' + data[1] + ' ' + data[2]
            # [memTotal, memFree, 1min, 5min, 15min, maxVCore, activeVCore]
            load = [self.container.publishToHost(nodes[0], 'UTILIZATION')]
            for node in nodes[1:]:
               load += [self.container.publishToHost(node, 'UTILIZATION')]
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            weights = myConnector.getWeights('balance')
            vm = myConnector.getProfileData(data[1])
            myConnector.disconnect()

            selected = None
            if (self.lbMode == LBMode.RAIN):
               selected = load_balancer.rain_select(load, weights, vm)
            elif (self.lbMode == LBMode.ROUNDROBIN):
               selected = load_balancer.rr_select(load, vm)
            elif (self.lbMode == LBMode.CONSOLIDATE):
               selected = load_balancer.rain_select(load, (0) * 5, vm)
            elif (self.lbMode == LBMode.RANDOM):
               selected = load_balancer.rand_select(load, vm)

            if (selected == None):
               # Couldn't find a node to instantiate the vm
               self.request.sendall(websock.encode(Opcode.text, "-1"))
               return
            index = -1
            for i in range(0, len(nodes), 1):
               if (nodes[i][0] == selected[0]):
                  index = i
            selectedNode = nodes[index]
            response = self.container.publishToHost(selectedNode, message,     \
                                                    False).split(':')
            ip = networking.getIPFromDHCP(response[1])
            myConnector.connect()
            myConnector.updateInstanceIP(response[2], ip)
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, ip))

        # for debugging purposes, lets print out the data for all other cases
        elif (data[0] == 'GETUSERINSTANCES'):
            username = data[1]
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect() 
            instances = myConnector.getUserInstances(username)
            for instance in eval(instances):
               node = myConnector.getNodeByName(instance[2]) 
               nodeAddr = node[1].split(':')
               nodeAddr = (nodeAddr[0],int(nodeAddr[1]))
               message = 'CHECKINSTANCE ' + instance[0]
               response = self.container.publishToHost(nodeAddr, message) 
               if (response.split(':')[1] == 'error' and instance[1] != '-1'):
                  myConnector.deleteInstance(instance[0])
            instances = myConnector.getUserInstances(username)
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, username + ':' +  \
                                 instances))

        # the user has requested that an instance be destroyed.
        # a message should be relayed to the node hosting the instance.
        elif (data[0] == 'DESTROYINSTANCE'):
            username = data[1]
            domain = data[2]
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            instances = myConnector.getUserInstances(username)
            result = 'error'
            for instance in eval(instances):
               if (instance[0] == domain):
                  node = myConnector.getNodeByName(instance[2])
                  nodeAddr = node[1].split(':')
                  nodeAddr = (nodeAddr[0],int(nodeAddr[1]))
                  message = 'DESTROY ' + instance[0]
                  self.container.publishToHost(nodeAddr, message)
                  result = 'success'
                  break
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, result))

        # retrieve the RAIN constants from the database and send them to the
        # caller
        elif (data[0] == 'RAINCONSTANTS'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            weights = myConnector.getWeights('balance')
            result = ''
            for weight in weights:
               result += str(weight) + ';'
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, result[0:-1]))

        elif (data[0] == 'CHANGELBMODE'):
            mode = data[1]
            try:
               self.lbMode = LBMode[mode] 
            except:
               print(mode,"is not a valid load balance mode.")

        elif (data[0] == 'UPDATERAIN'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            myConnector.updateWeights('balance', data[1:])
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, '0'))

        elif (data[0] == 'IMAGELIST'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            images = myConnector.getImages()
            myConnector.disconnect()
            result = ''
            for image in images:
               result += image[0] + ';'
            self.request.sendall(websock.encode(Opcode.text, result[0:-1]))

        elif (data[0] == 'SAVEPROFILE'):
            #name = data[1]
            #title = data[2]
            #desc = data[3]
            #ram = data[4]
            #vcpu = data[5]
            #image = data[6]
            #myConnector = mysql(self.container.addr[0], 3306)
            #myConnector.connect()
            #myConnector.insertProfile(name, title, desc, ram, vcpu, image)
            #myConnector.disconnect()
            print(data)

        elif (data[0] == 'IMPORTIMAGE'):
            url = data[1]
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            storageNodes = myConnector.getStorageNodes()
            myConnector.disconnect()
            # Figure out what to do with multiple storage nodes
            nodeAddr = storageNodes[0][1].split(':')
            nodeAddr = (nodeAddr[0],int(nodeAddr[1]))
            message = 'IMPORTIMAGE ' + url
            res = self.container.publishToHost(nodeAddr, message, False)

        elif (data[0] == 'PROFILEINFO'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            profile = myConnector.getProfile(data[1])
            myConnector.disconnect()
            result = ''
            for datum in profile:
               result += str(datum) + ';'
            self.request.sendall(websock.encode(Opcode.text, result[0:-1]))
        
        elif (data[0] == 'DEPLOY'):
            role = data[1]
            macs = data[2].split(';')[0:-1]
            for mac in macs:
               oldDHCPTime = networking.getDHCPRenewTime(mac)
               tftpDir = constants.get('default.tftpdir')
               shutil.copyfile('pxetemplate.cfg', tftpDir +                    \
                               '/pxelinux.cfg/01-' + mac)
               fname = tftpDir + '/pxelinux.cfg/01-' + mac
               for line in fileinput.input(fname, inplace=True):
                  if '<ROLE>' in line:
                     print(line.replace('<ROLE>', role), end='')
                  elif '<SERVER_IP>' in line:
                     print(line.replace('<SERVER_IP>',                         \
                                        self.container.addr[0]),               \
                                        end='')
                  else:
                     print(line, end='')
               t = threading.Thread(target = self.detectDHCPRenew,             \
                                    args = (mac, oldDHCPTime, ))
               t.start()
            self.request.sendall(websock.encode(Opcode.text, '0'))

        else:
            print('DATA:',data)

        return

    '''
    detectDHCPRenew(mac, time) ---
        Expected action:
           Read the DHCP log to determine if a particular
           MAC address has been assigned a new IP address.
           Once a new IP has been issued then it is safe
           to remove any PXE configurations for this node.

           Explanation: This is used for deployment.  We assume
           That after the node boots and gets configured over 
           PXE then it is okay to discard the configuration
           so that the node does not get redeployed on the next
           boot

        Expected positional arguments:
           mac - The MAC address of the node in question
           time - The previous time that the node received an IP address

        Expected return value:
           None
    '''
    def detectDHCPRenew(self, mac, time):
        changed = False
        while (not changed):
           newTime = networking.getDHCPRenewTime(mac)
           if newTime != time:
              changed = True
              print('Detected DHCP renew of MAC:', mac)
        sleep(120)
        os.remove(constants.get('default.tftpdir') + '/pxelinux.cfg/01-' + mac)
        print('Removed PXE configuration')

    '''
    processTraditionalRequest(data) ---
        Expected action:
           Process incoming messages from another physical node
           relay these messages to other nodes if need
           be and return a response to the caller

        Expected positional arguments:
           data - the raw message

        Expected return value:
           None
    '''
    def processTraditionalRequest(self, data):
        client = self.client_address
        events = self.container.events
        clients = self.container.clients

        # check if the request is an event call
        if (events.contains(data[0])):
            func = events.get(data[0])
            params = []
            for datum in data[1:]:
                params += [datum]

            # call the function and get the result
            response = str(func(data[0],params))
               
            if (response != None):
                # send the result to the caller
                self.request.sendall(response.encode('UTF8'))

        # check if the request is a query for the service role
        # (PUBLISHER | SUBSCRIBER)
        elif (data[0] == 'ROLE'):
            self.request.sendall(self.container.role.encode('UTF8'))

        elif (data[0] == 'INSTANTIATE'):
            print("INSTANTIATE TRADITIONAL")
            self.container.cleanupClients()
            nodes = clients.get('COMPUTE')
            # Message style:
            # INSTANTIATE <VM_NAME> <USER_NAME>
            message = data[0] + ' ' + data[1] + ' ' + data[2]
            # [memTotal, memFree, 1min, 5min, 15min, maxVCore, activeVCore]
            load = [self.container.publishToHost(nodes[0], 'UTILIZATION')]
            for node in nodes[1:]:
               load += [self.container.publishToHost(node, 'UTILIZATION')]
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            weights = myConnector.getWeights('balance')
            vm = myConnector.getProfileData(data[1])
            myConnector.disconnect()

            selected = None
            if (self.lbMode == LBMode.RAIN):
               selected = load_balancer.rain_select(load, weights, vm)
            elif (self.lbMode == LBMode.ROUNDROBIN):
               selected = load_balancer.rr_select(load, vm)
            elif (self.lbMode == LBMode.CONSOLIDATE):
               selected = load_balancer.rain_select(load, weights, vm)
            elif (self.lbMode == LBMode.RANDOM):
               selected = load_balancer.rand_select(load, vm)

            print("SELECTED:",selected)

            if (selected == None):
               # Couldn't find a node to instantiate the vm
               self.request.sendall('-1'.encode('UTF8'))
               return
            index = -1
            for i in range(0, len(nodes), 1):
               if (nodes[i][0] == selected[0]):
                  index = i
            selectedNode = nodes[index]
            response = self.container.publishToHost(selectedNode, message,     \
                                                    False).split(':')
            print("RESPONSE:",response)
            ip = networking.getIPFromDHCP(response[1])
            print("IP:", ip)
            myConnector.connect()
            myConnector.updateInstanceIP(response[2], ip)
            myConnector.disconnect()
            self.request.sendall(ip.encode('UTF8'))

        # check if the caller is requesting a nonce for authorization
        elif (data[0] == 'AUTH'):
            nonce = auth.generateNonce()
            self.container._nonce = nonce
            self.request.sendall(nonce.encode('UTF8'))

        # check if the caller is requesting authorization for subscription
        elif (data[0] == 'SUBSCRIBE'):
            r = data[4].encode('UTF8')
            m = auth.decrypt(r).decode('UTF8')[1:].split(':')[1]
            if (m == self.container._nonce):
                # we can consider this subscriber to be authentic
                if (len(data) == 5): # should be 5 values
                    # data[3] is the group name
                    if (clients.contains(data[3])):
                        c = clients.get(data[3])
                        c.append((data[1], int(data[2])))
                    else:
                        c = [(data[1], int(data[2]))]
                        clients.append((data[3], c))

        # check if the caller is sending a heartbeat
        elif (data[0] == 'HEARTBEAT'):
            # check if the client is still registered
            response = data[0]
            if (len(clients.collection()) == 0):
               response = 'SUBSCRIBE'
            else:
               found = False
               for group in clients.collection():
                  for ip in clients.get(group):
                     if (ip[0] == data[1] and str(ip[1]) == data[2]):
                        found = True
               if (not found):
                  response = 'SUBSCRIBE'
            self.request.sendall(response.encode('UTF8'))
        
        # check if an instance is running
        elif (data[0] == 'CHECKINSTANCE'):
            virtcon = libvirt.openReadOnly(None)
            if (virtcon == None):
               self.request.sendall('error'.encode('UTF8'))
            try:
               virtcon.lookupByName(data[1])
               self.request.sendall('success'.encode('UTF8'))
            except:
               self.request.sendall('error'.encode('UTF8'))
            virtcon.close()

        else:
            print('DATA:',data)

        return
