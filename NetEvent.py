# NetEvent API for building cloud middleware.
# Developed by Gabriel Jacob Loewen
# Copyright 2013 Gabriel Jacob Loewen

import socket, socketserver, threading, auth, time
from dictionary import *
from datetime import datetime

# Mapping from event name to function
events = Dictionary()

# Mapping from group name to list if clients
clients = Dictionary()

# Subscription identifier
subscription = ""

role = ""

nonce = ""

# Retreive the private IP of this system
def getIP():
   return socket.gethostbyname(socket.gethostname())

# Main class for NetEvent
class NetEvent():

   # Constructor, creates the TCP server
   def __init__(self, port = 0, r = "CLIENT"):
      global role
      role = r
      self.server = socketserver.TCPServer((getIP(), port), EventHandler)
      self.port = self.server.server_address[1]
      self.server.isDaemon = True
      self.start()

   # Start thread for handling requests
   def start(self):
      self.thread = threading.Thread(target = self.serve)
      self.thread.start()
      
   # Continuously handles requests
   def serve(self):
      while 1:
         self.server.handle_request()

   def getClusterList(self):
      global clients
      ret = ''
      for key in clients.collection():
         ret += key + ';'
      return ret[:-1]

   # Register a possible event
   # Name - name of event used as a key
   # Event - function identifier bound to the event name
   def registerEvent(self, name, event):
      global events
      events.append((name, event))

   # Publish a message containing data to a specific host
   def publishToHost(self, host, data):
      print("Sending data at time:",str(datetime.now()))
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
         print("Host not found.  Removing from collection.")
         rmGroups = []
         for key in clients.collection():
            ips = clients.get(key)
            for i in range(0, len(ips), 1):
               if (ips[i][0] == host[0]):
                  ips.pop(i)
                  if (len(ips) == 0):
                     rmGroups.append(key)
         for group in rmGroups:
            clients.remove(group)
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
   def subscribe(self, host, group):
      global getIP
      global subscription
      ip = getIP()
      self.subscription = host
      print(host)

      nonce = self.publishToHost(host, "AUTH")
      self.publishToHost(host, "SUBSCRIBE " + ip + " " + str(self.port) + " " + group + " " + auth.encrypt(nonce).decode("utf-8"))

   def getSubscription(self):
      try:
         return self.subscription
      except AttributeError:
         return -1

   def associateGroup(self, group):
      self.group=group
 
   def findController(self):
      global getIP
      ip = getIP()
      octets = ip.split(".")
      testOctet = 0
      found = False

      print("Searching for controller node", end="")
      while (found == False):
         if (testOctet == 256):
            testOctet = 0
         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

   def getClientList(self):
      global clients
      listString = ''
      for group in clients:
         clist = ''
         for client in clients[group]:
            clist += '(' + client[0] + ',' + client[1] + ');'
         listString += group + ":" + clist
      return listString

class EventHandler(socketserver.BaseRequestHandler):
   # Handle external requests
   def handle(self):
      global clients
      global events
      global role
      global nonce
      self.data = self.request.recv(1024).decode().split()
      print("Before trigger:",str(datetime.now()))
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
      print("After trigger:",str(datetime.now()))
      self.request.close()
