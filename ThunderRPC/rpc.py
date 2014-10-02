# rpc.py - Server handlers for thunder RPC implementation
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import auth, socket, socketserver, threading, libvirt, load_balancer, subprocess
from websocket import *
from mysql_support import *


# Each request should be given an independent thread, each handled by
# the RequestHandler class
class ThunderRPCServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

# Handler class for handling incoming connections
class RequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.daemon_threads = True
        self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY, True)
        self.request.setblocking(1)
        return

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

    # the data is coming from the web interface.  the web interface should only
    # be able to retrieve data from clusters and request virtual machines
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
            p = subprocess.Popen("./capturemacs.sh", stdout=subprocess.PIPE,                \
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            macs = out.decode().rstrip().split('\n')
            result = ""
            for mac in macs:
                result+=mac.strip() + ";"
            print(result)
            self.request.sendall(websock.encode(Opcode.text, result[:-1]))

        elif (data[0] == 'INSTANTIATE'):
            nodes = clients.get("COMPUTE")
            message = data[0] + ' ' + data[1] + ' ' + data[2]
            load = [self.container.publishToHost(nodes[0], "UTILIZATION")]
            for i in range(1,len(nodes),1):
               load += [self.container.publishToHost(nodes[i], "UTILIZATION")]
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            weights = myConnector.getWeights("balance")
            myConnector.disconnect()
            index = load_balancer.select(load, weights)
            selectedNode = nodes[index]
            response = self.container.publishToHost(selectedNode, message)
            self.request.sendall(websock.encode(Opcode.text, response))
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
               message = "CHECKINSTANCE " + instance[0]
               response = self.container.publishToHost(nodeAddr, message) 
               if (response.split(':')[1] == "error"):
                  myConnector.deleteInstance(instance[0])
            instances = myConnector.getUserInstances(username)
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, username+":"+instances))
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
                  message = "DESTROY " + instance[0]
                  self.container.publishToHost(nodeAddr, message)
                  result = 'success'
                  break
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, result))

        elif (data[0] == "MLBCONSTANTS"):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            weights = myConnector.getWeights("balance")
            result = ""
            for weight in weights:
               result += str(weight) + ";"
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, result[0:-1]))

        elif (data[0] == "UPDATEMLB"):
            myConnector = mysql(self.container.addr[0], 3306)
            myConnector.connect()
            myConnector.updateWeights("balance", data[1:])
            myConnector.disconnect()
            self.request.sendall(websock.encode(Opcode.text, "MLB Constants Update: SUCCESS"))

        else:
            print("DATA:",data)

        return

    def processTraditionalRequest(self, data):
        client = self.client_address
        events = self.container.events
        clients = self.container.clients

        # check if the request is an event call
        if (events.contains(data[0])):
            func = events.get(data[0])
            params = []
            for i in range(1, len(data), 1):
                params += [data[i]]

            # call the function and get the result
            response = func(data[0],params)
            respList = response.split()
               
            if (response != None):
                # send the result to the caller
                self.request.sendall(str(response).encode('UTF8'))

        # check if the request is a query for the service role
        # (PUBLISHER | SUBSCRIBER)
        elif (data[0] == 'ROLE'):
            self.request.sendall(self.container.role.encode('UTF8'))

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
            self.request.sendall(data[0].encode('UTF8'))

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
            print(data)

        return
