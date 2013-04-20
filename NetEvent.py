# NetEvent API for building cloud middleware.
# Developed by Gabriel Jacob Loewen
# Copyright 2013 Gabriel Jacob Loewen

import socket, socketserver, threading, auth, time
from dictionary import *

# Mapping from event name to function
events = Dictionary()

# Mapping from group name to list if clients
clients = Dictionary()

# Subscription identifier
subscription = ""

role = ""

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
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(host)
      # Send data
      s.send(data.encode())
      # Receive and process response
      response = s.recv(1024).decode()
      s.close()
      return '('+str(host[0])+':'+str(response)+')'

   # Publish a message containing data to all clients
   def publishToGroup(self, data, group):
      global clients
      responses = []
      if (clients.contains(group)):
         ipList = clients.get(group)
         for ip in ipList:
            responses.append(self.publishToHost(ip, data)+';')
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

      nonce = self.publishToHost(host, "SUBSCRIBE " + ip + " " + str(self.port) + " " + group)
      nonce = nonce[1:-1].split(':')[1]
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(host)
      m = auth.encrypt(nonce)
      print("m =",m)
      s.send(m)
      s.close()


   def getSubscription(self):
      try:
         return self.subscription
      except AttributeError:
         return -1

   def associateGroup(self, group):
      self.group=group
 
   def findMaster(self):
      global getIP
      ip = getIP()
      octets = ip.split(".")
      testOctet = 0
      found = False

      print("Searching for master node", end="")
      while (found == False and testOctet < 256):
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
         print("\nFound at", address)
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
      elif (self.data[0] == "SUBSCRIBE"):
         n = auth.generateNonce()
         self.request.sendall(n.encode())
         print("n =",n)
         if (m == r):
            if (len(self.data) == 4): 
               # The group exists
               if (clients.contains(self.data[3])):
                  c = clients.get(self.data[3])
                  c.append((self.data[1], int(self.data[2])))
               # The group does not exist
               else:
                  c = [(self.data[1], int(self.data[2]))]
                  clients.append((self.data[3], c))
      self.request.close()
