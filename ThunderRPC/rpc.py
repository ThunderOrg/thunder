# rpc.py - Server handlers for thunder RPC implementation
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import auth, socket, socketserver, threading
from websocket import *

# Each request should be given an independent thread, each handled by
# the RequestHandler class
class ThunderRPCServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    def setup(self):
        self.daemon_threads = true

# Handler class for handling incoming connections
class RequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY, True)
        return

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
            decodedData = websock.decode().strip()
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
            iface = self.container.interface
            fname = ['./macdump.sh', int(data[1]), iface]
            p = subprocess.Popen(fname, stdout=subprocess.PIPE,                \
                                 stderr=subprocess.PIPE)
            p.communicate()[0]
            fp = open("./mac.list", "r")
            result = ''
            for line in fp:
                result+=line.strip() + ";"
            fp.close()
            self.request.sendall(websock.encode(Opcode.text, result[:-1]))

        elif (data[0] == 'INSTANTIATE'):
            nodes = clients.get("Compute")
            message = data[0] + ' ' + data[1] + ' ' + data[2]
            # TODO: Node selection algorithm (Balance vs Consolidation)
            response = self.container.publishToHost(nodes[0], message)
            self.request.sendall(websock.encode(Opcode.text, response))
        # for debugging purposes, lets print out the data for all other cases
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

        else:
            print(data)

        return
