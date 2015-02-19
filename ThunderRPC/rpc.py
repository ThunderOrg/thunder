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
import threadpool
from websocket import *
from message import createMessage, parseMessage
from mysql_support import *
from time import sleep
from enum import Enum

locks = [0] * 5

class LBMode(Enum):
   RAIN=0
   ROUNDROBIN=1
   CONSOLIDATE=2
   RANDOM=3

'''
ThunderRPCServer(ThreadPoolMixIn, TCPServer) ---
Dummy class used to ensure per-request threading
'''
class ThunderRPCServer(threadpool.ThreadPoolMixIn, socketserver.TCPServer):
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
           None

        Expected return value:
           None
    '''
    def setup(self):
        self.daemon_threads = True
        self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY, True)
        self.request.setblocking(1)
        try:
           fp = open('./lb.conf', 'r')
           self.lbMode = LBMode[fp.read()]
           fp.close()
        except:
           self.lbMode = LBMode.RAIN
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
        self.data = self.request.recv(1024)
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
            decodedData = parseMessage(decodedData)
            if (ws):
                self.processWebsocketRequest(self.request, decodedData, websock)
            else:
                self.processTraditionalRequest(self.request, decodedData)
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
    def processWebsocketRequest(self, request, data, websock):
        clients = self.container.clients
        # check if the client is requesting data from a group
        if (data['cmd'] == 'EXECGROUP'):
            group = data['group']
            message = createMessage(cmd=data['remote_cmd'], args=data['remote_args'])
            res = self.container.publishToGroup(group, message)
            request.sendall(websock.encode(Opcode.text, res))

        # check if the client is requesting data from a node
        elif (data['cmd'] == 'EXECNODE'):
            node = (data['ip'], int(data['port']))
            message = createMessage(cmd=data['remote_cmd'], args=data['remote_args'])
            res = self.container.publishToHost(node, message)
            if ('result' in res):
               result = createMessage(result=res['result'])
            else:
               print("Result not in res? ", res)
               result = str(res).encode('UTF8')
            request.sendall(websock.encode(Opcode.text, result))

        # check if the client is requesting a list of clusters available
        elif (data['cmd'] == 'GROUPNAMES'):
            result = websock.encode(Opcode.text,                               \
                     createMessage(clusters=self.container.getClusterList()))
            request.sendall(result)

        # check if the client is requesting a list of nodes in a particular
        # cluster
        elif (data['cmd'] == 'NODESINGROUP'):
            clients = self.container.getClientList(data['cluster'])
            msg = createMessage(clients=clients)
            request.sendall(websock.encode(Opcode.text, msg))

        # check if the client is requesting the server to poll for mac
        # addresses, used for deployment
        elif (data['cmd'] == 'POLLMACS'):
            p = subprocess.Popen('./capturemacs.sh', stdout=subprocess.PIPE,   \
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            macs = out.decode().rstrip().split('\n')
            result = []
            for mac in macs:
                if (not mac.startswith(constants.get('default.vmMACPrefix'))):
                    result+=[mac.strip()]
            msg = createMessage(macs=result)
            request.sendall(websock.encode(Opcode.text, msg))

        elif (data['cmd'] == 'INSTANTIATE'):
            self.container.cleanupClients()
            nodes = clients.get('COMPUTE')
            # Message style:
            # INSTANTIATE <VM_NAME> <USER_NAME>
            message = createMessage(cmd=data['cmd'], vm=data['vm'], user=data['user'])
            utilization = createMessage(cmd='UTILIZATION')
            error = createMessage(ip=None)

            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            if (self.lbMode == LBMode.CONSOLIDATE):
               weights = [0] * 5
            elif (self.lbMode == LBMode.RAIN):
               weights = myConnector.getWeights('balance')
            vm = myConnector.getProfileData(data['vm'])
            myConnector.disconnect()
            load = [self.container.publishToHost(nodes[0], utilization)]
            for node in nodes[1:]:
               tmp = self.container.publishToHost(node, utilization)
               load += [tmp]

            selected = None
            index = -1
            if (self.lbMode == LBMode.RAIN or self.lbMode == LBMode.CONSOLIDATE):
               while (1):
                  # [memTotal, memFree, 1min, 5min, 15min, maxVCore, activeVCore]
                  selected = load_balancer.rain_select(load, weights, vm)
                  if (selected == None):
                     # Couldn't find a node to instantiate the vm
                     request.sendall(websock.encode(Opcode.text, error))
                     return

                  for i in range(0, len(nodes), 1):
                     if (nodes[i][0] == selected[0]):
                        index = i

                  if (index == -1):
                     request.sendall(websock.encode(Opcode.text, error))
                     return

                  # If we don't have enough locks, double it
                  if (index > len(locks)):
                     locks += [0] * len(locks) 

                  if (locks[index] == 0):
                     locks[index] = 1
                     break
                  else:
                     sleep(1)
                     load = [self.container.publishToHost(nodes[0], utilization)]
                     for node in nodes[1:]:
                        load += [self.container.publishToHost(node, utilization)]

            elif (self.lbMode == LBMode.ROUNDROBIN):
               selected = load_balancer.rr_select(load, vm)
               if (selected == None):
                  # Couldn't find a node to instantiate the vm
                  request.sendall(websock.encode(Opcode.text, error))
                  return

               for i in range(0, len(nodes), 1):
                  if (nodes[i][0] == selected[0]):
                     index = i

            elif (self.lbMode == LBMode.RANDOM):
               selected = load_balancer.rand_select(load, vm)
               if (selected == None):
                  # Couldn't find a node to instantiate the vm
                  request.sendall(websock.encode(Opcode.text, error))
                  return

               for i in range(0, len(nodes), 1):
                  if (nodes[i][0] == selected[0]):
                     index = i

            if (index == -1):
               request.sendall(websock.encode(Opcode.text, error))
           
            selectedNode = nodes[index]
            response = self.container.publishToHost(selectedNode, message, False)

            if (self.lbMode == LBMode.RAIN or self.lbMode == LBMode.CONSOLIDATE):
               locks[index] = 0

            response = response['result']
            ip = ''
            if ('mac' in response and response['mac'] != ''):
               ip = networking.getIPFromARP(response['mac'])
            myConnector.connect()
            myConnector.updateInstanceIP(response['domain'], ip)
            myConnector.disconnect()
            request.sendall(websock.encode(Opcode.text, createMessage(ip=ip)))

        elif (data['cmd'] == 'GETUSERINSTANCES'):
            username = data['user']
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect() 
            instances = myConnector.getUserInstances(username)
            for instance in eval(instances):
               node = myConnector.getNodeByName(instance[2]) 
               nodeAddr = node[1].split(':')
               nodeAddr = (nodeAddr[0],int(nodeAddr[1]))
               message = createMessage(cmd='CHECKINSTANCE', domain=instance[0])
               response = self.container.publishToHost(nodeAddr, message) 
               if (response['result'] == 'error' and instance[1] != '-1'):
                  myConnector.deleteInstance(instance[0])
            instances = myConnector.getUserInstances(username)
            myConnector.disconnect()
            message = createMessage(user=username, instances=instances)
            request.sendall(websock.encode(Opcode.text, message)) 

        # the user has requested that an instance be destroyed.
        # a message should be relayed to the node hosting the instance.
        elif (data['cmd'] == 'DESTROYINSTANCE'):
            username = data['user']
            domain = data['domain']
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            instances = myConnector.getUserInstances(username)
            result = 'error'
            print(data)
            for instance in eval(instances):
               if (instance[0] == domain):
                  node = myConnector.getNodeByName(instance[2])
                  nodeAddr = node[1].split(':')
                  nodeAddr = (nodeAddr[0],int(nodeAddr[1]))
                  message = createMessage(cmd='DESTROY', domain=instance[0])
                  self.container.publishToHost(nodeAddr, message)
                  result = 'success'
                  break
            message = createMessage(result=result)
            myConnector.disconnect()
            request.sendall(websock.encode(Opcode.text, message))

        # retrieve the RAIN constants from the database and send them to the
        # caller
        elif (data['cmd'] == 'RAINCONSTANTS'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            weights = myConnector.getWeights('balance')
            result = []
            for weight in weights:
               result += [weight]
            myConnector.disconnect()
            message = createMessage(result=result)
            request.sendall(websock.encode(Opcode.text, message))

        elif (data['cmd'] == 'GETLBMODE'):
            try:
               fp = open('lb.conf', 'r')
               mode = fp.read()
               fp.close()
               message = createMessage(lbmode=mode);
            except:
               fp = open('lb.conf', 'w')
               fp.write("RAIN")
               fp.close()
               message = createMessage(lbmode="RAIN");
            request.sendall(websock.encode(Opcode.text, message))

        elif (data['cmd'] == 'CHANGELBMODE'):
            mode = data['mode']
            try:
               self.lbMode = LBMode[mode] 
               fp = open('lb.conf', 'w')
               fp.write(mode)
               fp.close()
            except:
               raise
               print(mode,"is not a valid load balance mode.")
            message = createMessage(result=0)
            request.sendall(websock.encode(Opcode.text, message))

        elif (data['cmd'] == 'UPDATERAIN'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            myConnector.updateWeights('balance', data['constants'])
            myConnector.disconnect()
            # TODO: Failutes?
            request.sendall(websock.encode(Opcode.text, createMessage(result=0)))

        elif (data['cmd'] == 'IMAGELIST'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            images = myConnector.getImages()
            myConnector.disconnect()
            result = []
            for image in images:
               result += [image[0]]
            message = createMessage(result=result)
            request.sendall(websock.encode(Opcode.text, message))

        elif (data['cmd'] == 'SAVEPROFILE'):
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

        elif (data['cmd'] == 'IMPORTIMAGE'):
            url = data['url']
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            storageNodes = myConnector.getStorageNodes()
            myConnector.disconnect()
            # Figure out what to do with multiple storage nodes
            nodeAddr = storageNodes[0][1].split(':')
            nodeAddr = (nodeAddr[0],int(nodeAddr[1]))
            message = createMessage(cmd='IMPORTIMAGE', url=url)
            res = self.container.publishToHost(nodeAddr, message, False)

        elif (data['cmd'] == 'PROFILEINFO'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            profile = myConnector.getProfile(data['profile'])
            myConnector.disconnect()
            result = []
            for datum in profile:
               result += [datum]
            message = createMessage(result=result)
            request.sendall(websock.encode(Opcode.text, message))
        
        elif (data['cmd'] == 'DEPLOY'):
            role = data['role']
            macs = data['macs']
            print(macs)
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
            message = createMessage(result=1)
            request.sendall(websock.encode(Opcode.text, message))

        elif (data['cmd'] == "REBOOTNODE"):
            p = subprocess.Popen(['sudo','reboot'], stdout=subprocess.PIPE,             \
                                 stderr=subprocess.PIPE)
            out = p.communicate()
            print(out)
            
        else:
            print('DATA:',data)

        request.close()
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
    def processTraditionalRequest(self, request, data):
        client = self.client_address
        events = self.container.events
        clients = self.container.clients

        # check if the request is an event call
        if (events.contains(data['cmd'])):
            func = events.get(data['cmd'])

            response = func(data)
            # send the result to the caller
            request.sendall(createMessage(result=response))

        # check if the request is a query for the service role
        # (PUBLISHER | SUBSCRIBER)
        elif (data['cmd'] == 'ROLE'):
            message = createMessage(role=self.container.role)
            request.sendall(message.encode('UTF8'))

        # check if the caller is requesting a nonce for authorization
        elif (data['cmd'] == 'AUTH'):
            nonce = auth.generateNonce()
            self.container._nonce = nonce
            request.sendall(createMessage(nonce=nonce))

        # check if the caller is requesting authorization for subscription
        elif (data['cmd'] == 'SUBSCRIBE'):
            r = data['nonce'].encode('UTF8')
            m = auth.decrypt(r).decode('UTF8')
            if (m == self.container._nonce):
                # we can consider this subscriber to be authentic
                if (len(data) == 5): # should be 5 values
                    # data[3] is the group name
                    if (clients.contains(data['group'])):
                        c = clients.get(data['group'])
                        c.append((data['ip'], data['port']))
                    else:
                        c = [(data['ip'], int(data['port']))]
                        clients.append((data['group'], c))
            request.sendall(createMessage(result=0)) 

        # check if the caller is sending a heartbeat
        elif (data['cmd'] == 'HEARTBEAT'):
            # check if the client is still registered
            response = data['cmd']
            if (len(clients.collection()) == 0):
               response = 'SUBSCRIBE'
            else:
               found = False
               for group in clients.collection():
                  for ip in clients.get(group):
                     if (ip[0] == data['ip'] and ip[1] == data['port']):
                        found = True
               if (not found):
                  response = 'SUBSCRIBE'
            message = createMessage(result=response)
            request.sendall(message)

        elif (data['cmd'] == 'UPDATERAIN'):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            myConnector.updateWeights('balance', data[1:])
            myConnector.disconnect()
            message = createMessage(result=0)
            request.sendall(message)

        elif (data['cmd'] == 'INSTANTIATE'):
            self.container.cleanupClients()
            nodes = clients.get('COMPUTE')
            # Message style:
            # INSTANTIATE <VM_NAME> <USER_NAME>
            message = createMessage(cmd=data['cmd'], vm=data['vm'], user=data['user'])
            utilization = createMessage(cmd='UTILIZATION')
            error = createMessage(ip=None)

            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            if (self.lbMode == LBMode.CONSOLIDATE):
               weights = [0] * 5
            elif (self.lbMode == LBMode.RAIN):
               weights = myConnector.getWeights('balance')
            vm = myConnector.getProfileData(data['vm'])
            myConnector.disconnect()
            load = [self.container.publishToHost(nodes[0], utilization)]
            for node in nodes[1:]:
               tmp = self.container.publishToHost(node, utilization)
               load += [tmp]

            selected = None
            index = -1
            if (self.lbMode == LBMode.RAIN or self.lbMode == LBMode.CONSOLIDATE):
               while (1):
                  # [memTotal, memFree, 1min, 5min, 15min, maxVCore, activeVCore]
                  selected = load_balancer.rain_select(load, weights, vm)
                  if (selected == None):
                     # Couldn't find a node to instantiate the vm
                     request.sendall(error)
                     return

                  for i in range(0, len(nodes), 1):
                     if (nodes[i][0] == selected[0]):
                        index = i

                  if (index == -1):
                     request.sendall(error)
                     return

                  # If we don't have enough locks, double it
                  if (index > len(locks)):
                     locks += [0] * len(locks) 

                  if (locks[index] == 0):
                     locks[index] = 1
                     break
                  else:
                     sleep(1)
                     load = [self.container.publishToHost(nodes[0], utilization)]
                     for node in nodes[1:]:
                        load += [self.container.publishToHost(node, utilization)]
          
            elif (self.lbMode == LBMode.ROUNDROBIN):
               selected = load_balancer.rr_select(load, vm)
               if (selected == None):
                  # Couldn't find a node to instantiate the vm
                  request.sendall(error)
                  return

               for i in range(0, len(nodes), 1):
                  if (nodes[i][0] == selected[0]):
                     index = i

            elif (self.lbMode == LBMode.RANDOM):
               selected = load_balancer.rand_select(load, vm)
               if (selected == None):
                  # Couldn't find a node to instantiate the vm
                  request.sendall(error)
                  return

               for i in range(0, len(nodes), 1):
                  if (nodes[i][0] == selected[0]):
                     index = i

            if (index == -1):
               request.sendall(error)
           
            selectedNode = nodes[index]
            response = self.container.publishToHost(selectedNode, message, False)

            if (self.lbMode == LBMode.RAIN or self.lbMode == LBMode.CONSOLIDATE):
               locks[index] = 0

            ip = ''
            response = response['result']
            if ('mac' in response and response['mac'] != ''):
               ip = networking.getIPFromARP(response['mac'])
            myConnector.connect()
            myConnector.updateInstanceIP(response['domain'], ip)
            myConnector.disconnect()
            request.sendall(createMessage(ip=ip))

        elif (data['cmd'] == 'CHANGELBMODE'):
            mode = data['mode']
            try:
               self.lbMode = LBMode[mode] 
               fp = open('lb.conf', 'w')
               fp.write(mode)
               fp.close()
            except:
               print(mode,"is not a valid load balance mode.")
            message = createMessage(result=0)
            request.sendall(message)

        # check if an instance is running
        elif (data['cmd'] == 'CHECKINSTANCE'):
            virtcon = libvirt.openReadOnly(None)
            error = createMessage(result='error')
            success = createMessage(result='success')
            if (virtcon == None):
               request.sendall(error)
            try:
               virtcon.lookupByName(data['domain'])
               request.sendall(success)
            except:
               request.sendall(error)
            virtcon.close()

        else:
            print('DATA:',data)

        request.close()
        return
