# NetEvent API for building cloud middleware.
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Lab
# Copyright 2014 Gabriel Jacob Loewen

import auth, re, mysql.connector, threading, socket, socketserver, sys, subprocess, events as builtinEvents
from dictionary import *
from websocket import *
from time import sleep

# ensure that the address used by the service can be reused if it crashes.
socketserver.TCPServer.allow_reuse_address = True

# default port of the server
SERVER_PORT = 49687

class NetEvent(threading.Thread):
   def __init__(self, port = 0, interface = 'eth0', role = 'CLIENT', group = 'Cloud', publisherSubnet = '1'):
      # invoke the constructor of the threading superclass
      super(NetEvent, self).__init__()

      # set the interface variable, which is the interface that we want to bind the service to
      self._interface = interface

      # set the role ('CLIENT' | 'ADMIN')
      self._role = role

      # get the IP address of the system
      self._IP = self.getIP(interface)

      # create a TCP server, and bind it to the address of the desired interface
      self._server = socketserver.TCPServer((self._IP, port), self.NetEventServer)
      self._server._NetEventInstance = self

      # workaround for getting the port number for auto-assigned ports (default behavior for clients)
      self._port = self._server.server_address[1]
      print("Binding to IP address - ", self._IP,":",self._port, sep='')

      # create a dictionary mapping an event name to a function
      self._events = Dictionary()

      # create a dictionary mapping a group name to an array of tuples (IP,Port)
      # these tuples represent the clients that are connecting to this service
      # if the role of this service is CLIENT then this dictionary should always be empty.
      self._clients = Dictionary()

      # register some builtin events for metadata aggregation
      self.registerEvent("UTILIZATION", builtinEvents.utilization)
      self.registerEvent("SYSINFO", builtinEvents.sysInfo)

      # associate with a group
      self._group = group

      # set the default publisher to None
      self._publisher = None

      # set the default publishers subnet
      self._publisherSubnet = publisherSubnet

      # set an initial nonce value.  this should always be updated when adding a new client.
      self._nonce = ''

      # start the thread
      self.start()
      return

   # getters and setters
   @property
   def clients(self):
      return self._clients
   
   @property
   def events(self):
      return self._events

   @property
   def interface(self):
      return self._interface
  
   @property
   def role(self):
      return self._role
  
   @property
   def address(self):
      return (self._IP, self._port)
  
   @property
   def group(self):
      return self._group

   @group.setter
   def group(self, value):
      self._group = value
  
   @property
   def publisher(self):
      return self._publisher

   @publisher.setter
   def publisher(self, value):
      self._publisher = value
  
   @property
   def publisherSubnet(self):
      return self._publisherSubnet

   # deconstructor
   def __del__(self):
      self.running = False
      return

   # retrieve a semicolon delimeted list of clusters
   def getClusterList(self):
      ret = ''
      self.cleanupClients()
      for cluster in self.clients.collection():
         ret += cluster + ';'
      return ret[:-1].strip()
   
   # Retrieve a semicolon delimeted list of clients
   def getClientList(self, group):
      listString = ''
      clist = ''
      self.cleanupClients()
      for client in self.clients.get(group):
         clist += client[0] + ':' + str(client[1]) + ';';
      return clist[:-1].strip()

   # get the IP of the desired networking interface
   def getIP(self, interface):
      p = subprocess.Popen(['/sbin/ifconfig', interface.strip()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      ifconfig = p.communicate()[0]
      if (ifconfig):
         data = ifconfig.decode().split('\n')
         for item in data:
            item = item.strip()
            if (item.startswith('inet ')):
               return item.split(':')[1].split()[0]
      return '127.0.0.1'

   # get the MAC address of the desired networking interface
   def getMAC(self, interface):
      p = subprocess.Popen(['/sbin/ifconfig', interface.strip()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      ifconfig = p.communicate()[0]
      if (ifconfig):
         data = ifconfig.decode().split('\n')
         for item in data:
            itemArr = item.strip().split()
            found = False
            for field in itemArr:
               if (found):
                  return field.strip()
               elif (field.lower() == 'hwaddr'):
                  found = True
      return None
 
   # inherited from threading.Thread
   def run(self):
      self.running = True
      while (self.running):
         self._server.handle_request()
      self._server.shutdown()
      return
  
   # send a message to another machine running the NetEvent service
   def publishToHost(self, host, data):
      # open a socket connection
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(host)
      # encode the data before sending
      s.send(data.encode('UTF8'))
      # wait for a response from the host
      response = s.recv(1024).decode()
      s.close()
      # return a colon delimited string containing the IP address of the host and its response
      return host[0]+':'+str(response)

   def cleanupClients(self):
      # For each group in the list of clients, find the unavailable address and remove it.
      emptyGroups = []
      for grp in self.clients.collection():
         addresses = self.clients.get(grp)
         for addr in addresses:
            try:
               s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
               s.connect(addr)
               s.close()
            except:
               addresses.remove(addr)
               if (len(self.clients.get(grp)) == 0):
                  emptyGroups += [grp]
      # Any groups with no clients should be removed
      for grp in emptyGroups:
         del self.clients.collection()[grp]
  
   # publish data to an entire group
   def publishToGroup(self, group, data):
      ret = ''
      if (self.clients.contains(group)):
         addresses = self.clients.get(group)
         for addr in addresses:
            val = self.publishToHost(addr, data)
            if (val != None):
               ret += val+';'
      if (len(ret) > 0):
         return ret[:-1]
      else:
         return None
        
   # register an event by adding it to a dictionary (NAME->EVENT)
   def registerEvent(self, name, event):
      self.events.append((name, event))
      return
   
   # register client with a server (subscribe to a publisher)
   def registerClient(self, host, group):    
      # send an authorization request to the server.  The server should return a nonce value.
      nonce = self.publishToHost(host, 'AUTH')

      # encrypt the nonce with pre-shared key and send it back to the host.
      decVal = auth.encrypt(nonce).decode('UTF8')
      ret = self.publishToHost(host, 'SUBSCRIBE ' + self.address[0] + ' ' + str(self.address[1]) + ' ' + self.group + ' ' + decVal)
     
      # save the IP of the publisher.
      self.publisher = host
     
      # start a heartbeat for fault tolerance
      self.startHeartBeat()
      return
   
   # spin up another thread that will periodically ping the server to make sure that it is still alive.
   def startHeartBeat(self):
      self._heartBeatThread = threading.Thread(target = self.heartBeat)
      self._heartBeatThread.start()
      return
    
   # send a 'pulse' to the publisher.  If the publisher doesn't respond then maybe its IP has changed
   # in which case we can try to connect to it again by polling addresses on the network.
   def heartBeat(self):
      # if there is no publisher to ping then something bad happened.
      if (self.publisher == None):
         self.findPublisher()
         return
      
      alive = True
      while (alive):
         ret = self.publishToHost(self.publisher, "HEARTBEAT")
         if (ret == None):
            alive = False
        
         sleep(300)
      self.findPublisher()
      return
   
   # parse the local IP routing table for entries
   def ipRouteList(self):
      addresses = []
      p = subprocess.Popen(['/sbin/ip', 'route', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      iptable = p.communicate()[0]
      if (iptable):
         data = iptable.decode().split('\n')
         for line in data:
            lineArr = line.split()
            for i in range(0, len(lineArr), 1):
               if (lineArr[i].strip().lower == 'src'):
                  addresses += [lineArr[i+1]]
      return addresses
     
   # Attempt to locate a publisher (controller) on the network. 
   def findPublisher(self):
      print("Looking for publisher")
      # first load the ip addresses from the local iptables and try them.
      routingTable = self.ipRouteList()
      if (len(routingTable) > 0):
         for address in routingTable:
            if (self.testForPublisher(address)):
               # this address is a publisher. connect to it!
               print("Found at", address)
               self.registerClient((address, SERVER_PORT), self.group)
               return
     
      # we couldn't find the publisher in the local routing table.  perform a linear scan over the subnet.
      ip = self.getIP(self.interface)
      octets = ip.split('.')

      # Maybe the localhost is the publisher.  Test that first.
      testOctet = int(octets[3])
      address = octets[0] + '.' + octets[1] + '.' + self.publisherSubnet + '.' + str(testOctet)
      if (self.testForPublisher(address)):
         self.registerClient((address, SERVER_PORT), self.group)
         return
      else:
         testOctet = 1

      print("Testing", address)
      found = False
      while (not found):
         address = octets[0] + '.' + \
                   octets[1] + '.' + \
                   self.publisherSubnet + '.' + \
                   str(testOctet)
         print("Testing", address)
         if (self.testForPublisher(address)):
            # this address is a publisher.  connect to it!
            self.registerClient((address, SERVER_PORT), self.group)
            found = True
         else:
            testOctet+=1
            if (testOctet > 255):
               testOctet = 0
      return
   
   # test a particular address for liveness and an administrative role
   def testForPublisher(self, address):
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.settimeout(10)
      try:
         s.connect((address, SERVER_PORT))
         s.settimeout(None)
         s.sendall('ROLE'.encode('UTF8'))
         response = s.recv(6).decode('UTF8')
         if (response == 'ADMIN'):
            return True
      except:
         pass
      s.close()
      return False
      
   # Handler class for handling incoming connections
   class NetEventServer(socketserver.BaseRequestHandler):
      def setup(self):
         self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY, True)
         return
      
      def handle(self):
         self.container = self.server._NetEventInstance
         self.data = self.request.recv(1024)
         websock = websocket(self.request)
         decodedData = ''
         ws = False
       
         print(self.data)
 
         # Check to see if the data is coming over a websocket connection (cloud interface)
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
              
         # close the connection
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
            self.request.sendall(websock.encode(Opcode.text, self.container.getClusterList()))

         # check if the client is requesting a list of nodes in a particular cluster
         elif (data[0] == 'NODESINGROUP'):
            clients = self.container.getClientList(data[1])
            self.request.sendall(websock.encode(Opcode.text, clients))

         # check if the client is requesting the server to poll for mac addresses,
         # used for deployment
         elif (data[0] == 'POLLMACS'):
            iface = self.container.interface
            fname = ['./macdump.sh', int(data[1]), iface]
            p = subprocess.Popen(fname, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()[0]
            fp = open("./mac.list", "r")
            result = ''
            for line in fp:
                result+=line.strip() + ";"
            fp.close()
            self.request.sendall(websock.encode(Opcode.text, result[:-1]))

         elif (data[0] == 'GETIMAGES'):
            nasAddr = getNASAddress()
            if (nasAddr != None):
               # mount NAS images repo
               # store image listing in array
               # unmount NAS
               pass
 
         # for debugging purposes, lets print out the data for all other cases
         else:
            print(data)
         return
        
      def processTraditionalRequest(self, data):
         events = self.container.events
         clients = self.container.clients
        
         # check if the request is an event call
         if (events.contains(data[0])):
            func = events.get(data[0])
            params = []
            for i in range(1, len(data), 1):
               params += [data[i]]
              
            # call the function and get the result
            response = func(params)
 
            # send the result to the caller
            self.request.sendall(str(response).encode('UTF8'))
        
         # check if the request is a query for the service role (ADMIN | CLIENT)
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
         elif (data[0] == 'ALIVE'):
            self.request.sendall(data[0].encode('UTF8'))
        
         return
