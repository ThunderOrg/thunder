# NetEvent API for building cloud middleware.
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Lab
# Copyright 2014 Gabriel Jacob Loewen

import threading, socket, socketserver, sys, subprocess, events as builtinEvents
from dictionary import *

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
     print("Binding to IP address", self.IP)

     # create a TCP server, and bind it to the address of the desired interface
     self.server = socketserver.TCPServer((self.IP, port), self.NetEventServer)
     self.server._NetEventInstance = self

     # workaround for getting the port number for auto-assigned ports (default behavior for clients)
     self.port = self.server.server_address[1]

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
        data = ifconfig.decode().split("\n\t")
        for item in data:
           if (str(item).startswith('inet ')):
              return item.split()[1]
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
        self.container = self.server._NetEventInstance
        self.data = self.request.recv(1024)
        print("\n message from: " + self.client_address[0] + " - " + self.data.decode('utf-8') + "\n")
        self.request.close()

if (__name__ == "__main__"):
   ne = NetEvent(6667,'lo0')
   msg = ''
   while (msg != 'done'):
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect(('127.0.0.1',6667))
      msg = input("enter a msg: ")
      s.send(msg.encode('utf-8'))
      s.close()
