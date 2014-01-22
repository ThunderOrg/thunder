# NetEvent API for building cloud middleware.
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Lab
# Copyright 2014 Gabriel Jacob Loewen

import re, threading, socket, socketserver, sys, subprocess, events as builtinEvents
from dictionary import *
from websocket import *
from time import sleep
import struct
socketserver.TCPServer.allow_reuse_address = True

class NetEvent(threading.Thread):
  def __init__(self, port = 0, interface = "eth0", role = "CLIENT"):
     # invoke the constructor of the threading superclass
     super(NetEvent, self).__init__()

     # set the interface variable, which is the interface that we want to bind the service to
     self.interface = interface

     # set the role ('CLIENT' | 'ADMIN')
     self.role = role

     # get the IP address of the system
     self.IP = self.getIP(interface)

     # create a TCP server, and bind it to the address of the desired interface
     self.server = socketserver.TCPServer((self.IP, port), self.NetEventServer)
     self.server._NetEventInstance = self

     # workaround for getting the port number for auto-assigned ports (default behavior for clients)
     self.port = self.server.server_address[1]
     print("Binding to IP address - ", self.IP,":",port, sep='')

     # create some dictionaries to hold pointers to events and client data
     self.events = Dictionary()
     self.clients = Dictionary()

     # register some builtin events for metadata aggregation
     self.registerEvent("UTILIZATION", builtinEvents.utilization)
     self.registerEvent("SYSINFO", builtinEvents.sysInfo)

     # start the thread
     self.start()

  # deconstructor
  def __del__(self):
     self.running = False

  # get the IP of the desired networking interface
  def getIP(self, interface):
     p = subprocess.Popen(['/sbin/ifconfig', interface.strip()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
     ifconfig = p.communicate()[0]
     if (ifconfig):
        data = ifconfig.decode().split("\n")
        for item in data:
           item = item.strip()
           if (item.startswith('inet ')):
              print(item)
              return item.split(':')[1].split(' ')[0]
     return '127.0.0.1'

  # get the MAC address of the desired networking interface
  def getMAC(self, interface):
     p = subprocess.Popen(['/sbin/ifconfig', interface.strip()], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
     ifconfig = p.communicate()[0]
     if (ifconfig):
        data = ifconfig.decode().split("\n\t")
        for item in data:
           if (item.startswith('ether ')):
              return item.split()[1]
     return None
 
  # inherited from threading.Thread
  def run(self):
     self.running = True
     while (self.running):
        self.server.handle_request()
     self.server.shutdown()
     sys.exit()

  # register an event by adding it to a dictionary (NAME->EVENT)
  def registerEvent(self, name, event):
     self.events.append((name, event))

  # Handler class for handling incoming connections
  class NetEventServer(socketserver.BaseRequestHandler):
     def handle(self):
        self.request.setblocking(1)
        self.container = self.server._NetEventInstance
        self.data = self.request.recv(1024)
        print(self.data.decode('UTF-8'))
        websock = websocket(self.request)
        wsRequest = False
        decodedData = ''

        # Check to see if the data is coming over a websocket connection (cloud interface)
        # Get the decoded data
        if (websock.isHandshakePending(self.data)):
           print("Accepting websocket handshake")
           handshake = websock.handshake(self.data.decode())
           print(handshake)
           self.request.send(handshake)
           self.request.close()
           while (1):
              pass
           #decodedData = websock.decode()
           #print(decodedData)
           #wsRequest = True
           #if (not decodedData):
           #   self.request.close()
           #   return
        # Else, it could be coming from a peer (cloud server)
        else:
           decodedData = self.data.decode('UTF-8')

   #     x = self.request.recv(4096)
    #    print(x)
        #print(decodedData)

        # Send back a response
        #if (wsRequest):
           # Tell the server to terminate
        #   self.request.send(websock.encode(Opcode.terminate,''))
        #print("closed")
        #self.request.close()

if (__name__ == "__main__"):
   ne = NetEvent(6667, 'eth0', 'ADMIN')
   #msg = ''
   #while (msg != 'done'):
   #   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   #   s.connect(('127.0.0.1',6667))
   #   msg = input("enter a msg: ")
   #   s.send(msg.encode('utf-8'))
   #   s.close()
