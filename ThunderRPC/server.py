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
import glob
import os

failed = 0
total = 0
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

def printTable(direc,fname):
   table = server.publishToGroup('COMPUTE', 'UTILIZATION')
   for machine in table.split(';'):
      m = machine.split(':')
      print_to_file(direc,fname, m[0].split('.')[-1],round(float(m[1])/(1024*1024),2),round(float(m[2])/(1024*1024),2),m[3],m[4],m[5],m[6],m[7],sepa="\t")

def startVM(profile,direc,fname):
   global total
   global failed
   begin = round(time() * 1000)
   vm = server.publishToHost(server.addr, 'INSTANTIATE ' + profile + ' admin', False)
   turnaround = round(time() * 1000) - begin
   vm = vm.split(':')
   lock.acquire()
   if (vm[1] == ''):
      print_to_file(direc,fname, "VM" + str(total) + "\t\tFailed\t\t" + str(turnaround))
      failed += 1
   else:
      print_to_file(direc,fname, "VM" + str(total) + "\t\tSuccess\t\t" + str(turnaround))
   total += 1
   lock.release()

# Instantiate NetEvent and register the invoke event
server = ThunderRPC(role = 'PUBLISHER', group = 'CONTROLLER')
server.registerEvent('INVOKE', invoke)

def print_to_file(*data, sepa=' '):
   direc = data[0]
   fname = "./tests/"+direc+"/"+data[1]
   args = data[2:]
   fp = open(fname, 'a+')
   print(*args, sep=sepa, file=fp)
   fp.close()
   print(*args, sep=sepa)

profiles = ['ubuntu_bare_small', 'ubuntu_bare_medium', 'ubuntu_bare_large']
while(1):
   input("Press enter to start...")
   for fname in glob.glob('*.in'): 
      fp = open(fname, 'r')
      if (fname == 'random.in'):
         server.publishToHost(server.addr, 'CHANGELBMODE RANDOM', False)    
      elif (fname == 'rr.in'):
         server.publishToHost(server.addr, 'CHANGELBMODE ROUNDROBIN', False)    
      elif (fname == 'noemph.in'):
         server.publishToHost(server.addr, 'CHANGELBMODE CONSOLIDATE', False)    
      else:
         constants = ' '.join(map(lambda x: str(int(float(x)*100)),fp.read().split()))
         server.publishToHost(server.addr, 'UPDATERAIN ' + constants, False)    
         server.publishToHost(server.addr, 'CHANGELBMODE RAIN', False)    
      fp.close()

      if not os.path.exists("./tests/" + fname + "/"):
         os.makedirs("./tests/" + fname + "/")

      i = 35
      while (i >= 25):
         for x in range(0, 5, 1):
            total = 0
            failed = 0
            #print_to_file("DATA_"+str(i)+"_"+str(x), "Testing", i, "Instantiations")
            printTable(fname,"BEFORE_"+str(i)+"_"+str(x))
            threads = []
            for y in range(0, i, 1):
               p = random.choice(profiles)
               t = threading.Thread(target=startVM, args=(p,fname,"DATA_"+str(i)+"_"+str(x)))
               t.start()
               threads += [t]
               sleep(2)
      
            for thread in threads:
               thread.join()
      
            printTable(fname,"AFTER_"+str(i)+"_"+str(x))
            sleep(10)
            printTable(fname,"RESTART_BEFORE_"+str(i)+"_"+str(x))
            threads = []
            for z in range(0, failed, 1):
               p = random.choice(profiles)
               t = threading.Thread(target=startVM, args=(p,fname,"RESTART_DATA_"+str(i)+"_"+str(x)))
               t.start()
               threads += [t]
               sleep(2)

            for thread in threads:
               thread.join()

            printTable(fname,"RESTART_AFTER_"+str(i)+"_"+str(x))
            sleep(2)
            server.publishToGroup('COMPUTE', 'DESTROYALL')
            sleep(60)
         i -= 5
