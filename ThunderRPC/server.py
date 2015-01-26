#!/usr/bin/env python3

'''
server.py
-----------------
Cloud Controller (Zeus) component of Thunder
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
from thunder import *
import sys
import random
import threading
from time import time, sleep

success=0
total=0
lock = threading.Lock()

# Invoke a function and return the result.
def invoke(*params):
   tag = params[0]
   data = params[1]

   if (len(data) > 1):
      if (data[0] == 'CONTROL'):
         if (data[1] == 'GET_CLIENT_LIST'):
            return server.getClientList()
         elif (data[1] == 'GET_CLUSTER_LIST'):
            return server.getClusterList()
      elif (data[0] == 'GROUP'):
         return server.publishToGroup(params[2], params[1])
      elif (data[0] == 'HOST'):
         host = (params[1], int(params[2]))
         return server.publishToHost(host,params[3])
   # Invalid number of params.  Return error code.
   else:
      return None

def printTable(table):
   print("IP","RAM","Free","1min","5min","15min","#Cores","Active",sep="\t")
   for machine in table.split(';'):
      m = machine.split(':')
      print(m[0].split('.')[-1],round(float(m[1])/(1024*1024),2),round(float(m[2])/(1024*1024),2),m[3],m[4],m[5],m[6],m[7],sep="\t")
   print('----------')

def startVM(profile):
   global success
   global total
   begin = round(time() * 1000)
   vm = server.publishToHost(server.addr, 'INSTANTIATE ' + profile + ' admin', False)
   turnaround = round(time() * 1000) - begin
   vm = vm.split(':')
   print(vm[1], " ", profile," (",total,") took ", turnaround, "ms to instantiate.", sep="")
   lock.acquire()
   total+=1
   if (vm[1] != '-1'):
      success+=1
   print("Total:", total, "Failed:", total - success)
   lock.release()

# Instantiate NetEvent and register the invoke event
server = ThunderRPC(role = 'PUBLISHER', group = 'CONTROLLER')
server.registerEvent('INVOKE', invoke)

profiles = ['ubuntu_bare_small', 'ubuntu_bare_medium', 'ubuntu_bare_large']
while(1):
   n = int(input('n: '))
   #z = server.publishToGroup('COMPUTE', 'UTILIZATION')
   #printTable(z)
   for i in range(0, n, 1):
      p = random.choice(profiles)
      t = threading.Thread(target=startVM, args=(p,))
      t.start()
      sleep(1) 
