# ThunderRPC.py - Remote Procedure Call (RPC) API for building cloud middleware.
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

# TODO:  Break this into Server/Client modules

import auth, re, mysql.connector, threading, socket, socketserver, sys, subprocess, platform, struct
import events as builtinEvents
from dictionary import *
from websocket import *
from time import sleep
from config import *

# ensure that the address used by the service can be reused if it crashes.
socketserver.TCPServer.allow_reuse_address = True

# parse thunder config file
parseConfig('thunder.conf')

# default port of the server
SERVER_PORT = int(constants.get('server.port'))

class ThunderRPC(threading.Thread):
   def __init__(self, role = constants.get('default.role'), group = constants.get('default.group')):

      # invoke the constructor of the threading superclass
      super(ThunderRPC, self).__init__()

      # check the role of the service to determine the proper configuration
      if (role == 'PUBLISHER'):
          interface = constants.get('server.interface') 
          port = SERVER_PORT
      elif (role == 'SUBSCRIBER'):
          interface = constants.get('default.interface') 
          port = int(constants.get('default.port'))
      else:
          print("Invalid role identifer.  Must be either 'PUBLISHER' or 'SUBSCRIBER'")
          sys.exit(-1)

      # set the interface variable, which is the interface that we want to bind the service to
      self._interface = interface

      # set the role ('PUBLISHER' | 'SUBSCRIBER')
      self._role = role
      
      # get the IP address of the system
      self._IP = self.getIP(interface)

      # create a TCP server, and bind it to the address of the desired interface
      self._server = socketserver.TCPServer((self._IP, port), self.ThunderRPCServer)
      self._server._ThunderRPCInstance = self

      # workaround for getting the port number for auto-assigned ports (default behavior for clients)
      self._port = self._server.server_address[1]

      # create a dictionary mapping an event name to a function
      self._events = Dictionary()

      # create a dictionary mapping a group name to an array of tuples (IP,Port)
      # these tuples represent the clients that are connecting to this service
      # if the role of this service is SUBSCRIBER then this dictionary should always be empty.
      self._clients = Dictionary()

      print("Starting ThunderRPC Service (role = %s)" % role)
      print("-------------------------------------------------")
      print("Binding to IP address - %s:%s" % (self._IP, self._port))

      # register some builtin events for metadata aggregation
      self.registerEvent("UTILIZATION", builtinEvents.utilization)
      self.registerEvent("SYSINFO", builtinEvents.sysInfo)

      # associate with a group
      self._group = group

      # set the default publisher to None
      self._publisher = None

      # set an initial nonce value.  this should always be updated when adding a new client.
      self._nonce = ''

      if (role == 'PUBLISHER'):
          # startup a multicasting thread to respond to multicast messages
          self.mcastThread = threading.Thread(target = self.multicastThread)
          self.mcastThread.start()

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

   # get an unbound socket to send multicast messages
   def getMulticastingSender(self):
      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
      sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
      return sock

   # get a bound socket for receiving multicast messages
   def getMulticastingReceiver(self):
      MCAST_GRP = constants.get('default.mcastgrp')
      MCAST_PORT = int(constants.get('default.mcastport'))
      sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
      try:
         sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      except AttributeError:
         pass

      # bind to all adapters
      sock.bind(('0.0.0.0', MCAST_PORT))
      mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
      sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
      return sock

   def multicastThread(self):
      MCAST_GRP = constants.get('default.mcastgrp')
      MCAST_PORT = int(constants.get('default.mcastport'))
      receiver = self.getMulticastingReceiver()
      while 1:
         try:
            data, addr = receiver.recvfrom(1024)
            if (data.decode() == 'ROLE'):
               # pack the role up with the client IP
               response = self.role + "|" + addr[0]
               receiver.sendto(response.encode('UTF8'), addr)
         except:
            pass

   # Attempt to locate a publisher (controller) on the network. 
   def findPublisher(self):
      MCAST_GRP = constants.get('default.mcastgrp')
      MCAST_PORT = int(constants.get('default.mcastport'))
      sender = self.getMulticastingSender()
      sender.settimeout(5)
      found = False
      address = None
      while(not found):
         sender.sendto('ROLE'.encode('UTF8'), (MCAST_GRP, MCAST_PORT))
         try:
            data, addr = sender.recvfrom(1024)
            response = data.decode().split('|')
            if (response[0] == 'PUBLISHER'):
               address = (addr[0],SERVER_PORT)
               # if the service is bound globally, replace the IP with the correct one
               # also find the correct interface
               if (self.interface == 'ALL'):
                  self._IP = response[1]
               found = True
         except KeyboardInterrupt:
            raise
         except:
            continue
      self.registerClient(address, self.group)

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
      if (interface == 'ALL'):
         return '0.0.0.0'

      p = subprocess.Popen(['/sbin/ifconfig', interface.strip()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
               # find the MAC address from the ifconfig output
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
  
   # send a message to another machine running the ThunderRPC service
   def publishToHost(self, host, data):
      try:
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
      except:
         return None

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
               print("Removing inactive client `%s:%d'" % (addr[0],addr[1]))
               addresses.remove(addr)
               if (len(self.clients.get(grp)) == 0):
                  emptyGroups += [grp]
      # Any groups with no clients should be removed
      for grp in emptyGroups:
         print("Removing empty group `%s'" % grp)
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
      print("Registering event - `%s (%s)'" % (name, event.__name__))
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
         sleep(int(constants.get('heartbeat.interval')))
         ret = self.publishToHost(self.publisher, 'HEARTBEAT')
         if (ret == None):
            alive = False
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
     
   # Handler class for handling incoming connections
   class ThunderRPCServer(socketserver.BaseRequestHandler):
      def setup(self):
         self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY, True)
         return
      
      def handle(self):
         self.container = self.server._ThunderRPCInstance
         self.data = self.request.recv(1024)
         websock = websocket(self.request)
         decodedData = ''
         ws = False
 
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

            if (response != None):
                # send the result to the caller
                self.request.sendall(str(response).encode('UTF8'))
        
         # check if the request is a query for the service role (PUBLISHER | SUBSCRIBER)
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
        
         return