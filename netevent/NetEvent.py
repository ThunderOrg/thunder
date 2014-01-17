# NetEvent API for building cloud middleware.
# Developed by Gabriel Jacob Loewen
# Copyright 2013 Gabriel Jacob Loewen

import socket, socketserver, threading, auth, time, events as builtinEvents
from threading import Timer
from dictionary import *
from datetime import datetime
from time import sleep

# Enable debugging output
debug = True

# Mapping from event name to function
events = Dictionary()

# Mapping from group name to list if clients
clients = Dictionary()

# Subscription identifier
subscription = None

role = ""

nonce = ""

group = ""

# Retreive the private IP of this system
def getIP():
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.connect(("google.com",80))
   ip = s.getsockname()[0]
   s.close();
   return ip
   #return socket.gethostbyname(socket.gethostname())

# Main class for NetEvent
class NetEvent():

   # Constructor, creates the TCP server
   def __init__(self, port = 0, r = "CLIENT"):
      global role
      global group
      role = r
      print(getIP())
      self.server = socketserver.TCPServer((getIP(), port), EventHandler)
      self.port = self.server.server_address[1]
      self.server.isDaemon = True
      self.start()
      # Register some data aggregation events for cpu/ram utilization as well as general system info
      self.registerEvent("UTILIZATION", builtinEvents.utilization)
      self.registerEvent("SYSINFO", builtinEvents.sysInfo)

   # Retrieve a semicolon delimeted list of clusters
   def getClusterList(self):
      global clients
      ret = ''
      for cluster in clients.collection():
         ret += cluster + ';'
      return ret[:-1]

   # Retrieve the current subscription
   def getSubscription(self):
      try:
         return self.subscription
      except AttributeError:
         return -1

   # Retrieve a colon delimeted list of clients
   def getClientList(self):
      global clients
      listString = ''
      for group in clients:
         clist = ''
         for client in clients[group]:
            clist += '(' + client[0] + ',' + client[1] + ');'
         listString += group + ":" + clist
      return listString

   # Start thread for checking the controller node to ensure that it is still alive.
   def startFaultTolerance(self):
      self.lifeGuardThread = threading.Thread(target = self.lifeGuard)
      self.lifeGuardThread.start()

   def lifeGuard(self):
      global subscription
      global group
      alive = True
      while(alive):
         print("Checking host status")
         if (subscription != None):
            resp = self.publishToHost(subscription, "ALIVE")
            if (resp == None):
               alive = False
         sleep(300)
      print("Controller lost.  Starting search.")
      self.findController()

   # Start thread for handling requests
   def start(self):
      self.thread = threading.Thread(target = self.serve)
      self.thread.start()
      
   # Continuously handles requests
   def serve(self):
      while 1:
         self.server.handle_request()

   # Register a possible event
   # Name - name of event used as a key
   # Event - function identifier bound to the event name
   def registerEvent(self, name, event):
      global events
      events.append((name, event))

   # Publish a message containing data to a specific host
   def publishToHost(self, host, data):
      global group
      global clients
      global subscription
      try:
         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         s.connect(host)
         # Send data
         s.send(data.encode())
         # Receive and process response
         response = s.recv(1024).decode()
         s.close()
         return '('+str(host[0])+':'+str(response)+')'
      except:
         if (subscription == None or host[0] != subscription[0]):
            rmGroups = []
            for key in clients.collection():
               ips = clients.get(key)
               i = 0
               while (i<len(ips)):
                  if (ips[i][0] == host[0]):
                     ips.pop(i)
                     if (len(ips) == 0):
                        rmGroups.append(key)
                  i+=1
            for grp in rmGroups:
               clients.remove(grp)
         return None
                  
   # Publish a message containing data to all clients
   def publishToGroup(self, data, group):
      global clients
      responses = []
      if (clients.contains(group)):
         ipList = clients.get(group)
         for ip in ipList:
            val = self.publishToHost(ip, data)
            if (val != None):
               responses.append(val+';')
      ret = ''
      for response in responses:
         ret += response
      return ret[:-1]

   # Subscribe to a host
   def subscribe(self, host, grp):
      global getIP
      global subscription
      global aliveTimer
      global group

      group = grp
      ip = getIP()
      subscription = host
      print(host)

      nonce = self.publishToHost(host, "AUTH")
      self.publishToHost(host, "SUBSCRIBE " + ip + " " + str(self.port) + " " + group + " " + auth.encrypt(nonce).decode("utf-8"))
      self.startFaultTolerance()

   def associateGroup(self, group):
      self.group=group
 
   def findController(self):
      global getIP
      ip = getIP()
      octets = ip.split(".")
      testOctet = int(octets[3])
      found = False

      print("Searching for controller node", end="")
      while (found == False):
         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         if (testOctet == 256):
            testOctet = 0
         s.settimeout(10)
         address = octets[0] + '.' + octets[1] + '.1.' + str(testOctet)
         try:
            s.connect((address, 6667))
            s.settimeout(None)
            s.sendall("ROLE".encode())
            response = s.recv(1024).decode()
            if (response == "ADMIN"):
               found = True
         except socket.error:
            print(".", end="")
         s.close()
         testOctet += 1

      if (found == True):
         print("\nController found at", address)
         try:
            self.subscribe((address, 6667), self.group)
            return (address, 6667)
         except AttributeError:
            print("Please associate with a group first!")
            return -1
      else:
         return -1

class EventHandler(socketserver.BaseRequestHandler):
   # Handle external requests
   def handle(self):
      global clients
      global events
      global role
      global nonce
      self.data = self.request.recv(1024).decode().split()
      print(self.data)
      # data[0] -> command
      # data[1] ... data[n] -> args
      if (events.contains(self.data[0])):
         f = events.get(self.data[0])
         params = []
         for i in range(1, len(self.data), 1):
            params.append(self.data[i])
         response = f(params)
         self.request.sendall(str(response).encode())
      elif (self.data[0] == "ROLE"):
         self.request.sendall(role.encode())
      elif (self.data[0] == "AUTH"):
         nonce = auth.generateNonce()
         self.request.sendall(nonce.encode())
      elif (self.data[0] == "SUBSCRIBE"):
         r = self.data[4].encode("utf-8")
         m = auth.decrypt(r).decode("utf-8")[1:-1].split(':')[1]
         if (m == nonce):
            print("Authenticated")
            if (len(self.data) == 5): 
               # The group exists
               if (clients.contains(self.data[3])):
                  c = clients.get(self.data[3])
                  c.append((self.data[1], int(self.data[2])))
               # The group does not exist
               else:
                  c = [(self.data[1], int(self.data[2]))]
                  clients.append((self.data[3], c))
      elif (self.data[0] == "ALIVE"):
         self.request.sendall("Y".encode())

      self.request.close()
