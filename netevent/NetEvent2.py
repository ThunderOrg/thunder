import subprocess, re, sys, socket, socketserver, threading, auth, time, events as builtinEvents
from dictionary import *

# Set up socket server to reuse the connection.  Fixes ``Address unavailable'' issue.
socketserver.TCPServer.allow_reuse_address = True

class NetEvent(threading.Thread):
   # Constructor
   def __init__(self, port = 0, role = "CLIENT", interface = "eth0"):
     # Call the constructor of the base class.
     super(NetEvent, self).__init__()

     # Set the role (CLIENT or ADMIN)
     self.role = role

     # Create a TCP server.  Port 0 auto-chooses an available port.
     self.server = socketserver.TCPServer((self.getIP(interface), port), self.Handler)

     # Get the chosen port from the server address
     self.port = self.server.server_address[1]
     
     # Identify the server as a daemon, or system service.
     self.server.isDaemon = True
     
     # Create some dictionaries for managing events and clients.
     self.clients = Dictionary()
     self.events = Dictionary()

     # Register some data aggregation events for cpu/ram utilization as well as general system info
     self.registerEvent("UTILIZATION", builtinEvents.utilization)
     self.registerEvent("SYSINFO", builtinEvents.sysInfo)

     # Start the server thread.
     self.running = False
     self.start()
 
   # Deconstructor
   def __del__(self):
      # Try to make sure that the server stops
      self.running = False
      if (self.server):
         self.server.server_close()

   # Start the server thread.
   def run(self):
      self.running = True
      while (self.running):
         self.server.handle_request()
      sys.exit()

   # Register a possible event
   # Name - name of event used as a key
   # Event - function identifier bound to the event name
   def registerEvent(self, name, event):
      self.events.append((name, event))

   # Retreive the private IP of this system
   def getIP(self, interface):
      # Open ifconfig binary and retrieve the output
      p = subprocess.Popen("/sbin/ifconfig", stdout=subprocess.PIPE)
      ifconfig = p.communicate()[0].decode()

      # If for some reason the process does not exit, kill it.
      try:
         p.kill()
      except OSError:
         pass

      # Get every interface with its associated IP address and mask.
      interfaces = re.findall("^(\S+).*?inet addr:(\S+).*?Mask:(\S+)", ifconfig, re.S | re.M)

      # Look for the right interface, and return the IP address
      for data in interfaces:
         if (data[0] == interface):
            print("Using interface '"+interface+"'.  With address", data[1])
            return data[1]

      # Use localhost is interface does not exist
      print("Could not find interface '"+interface+"'.  Using localhost instead.")
      return '127.0.0.1'
  
   def handle(self):
      print(self.data)

   # Handle incoming data over the connection.
   class Handler(socketserver.BaseRequestHandler):
      def handle(self):
         self.data = self.request.recv(4096).decode('utf-8')
         # Determine the type of data being sent.  WebSocket frames or internal data.
         print(self.data)

# Testing
if (__name__ == "__main__"):
   ne = NetEvent(12345)
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.connect((ne.getIP('eth0'),12345))
   s.send("Testing".encode('utf-8'))
   s.close()
