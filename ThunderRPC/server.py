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
from networking import createMessage

failed = 0
total = 0
lock = threading.Lock()

server = ThunderRPC(role = 'PUBLISHER', group = 'CONTROLLER')

def printTable(direc,fname):
   table = server.publishToGroup('COMPUTE', createMessage(cmd='UTILIZATION'))
   for machine in table:
      m = machine['result']
      host = machine['_HOST_']
      print_to_file(direc,fname, host[0].split('.')[-1],round(float(m[0])/(1024*1024),2),round(float(m[1])/(1024*1024),2),m[2],m[3],m[4],m[5],m[6],sepa="\t")

def startVM(profile,direc,fname):
   global total
   global failed
   begin = round(time() * 1000)
   vm = server.publishToHost(server.addr, createMessage(cmd='INSTANTIATE', vm=profile, user='admin'), False)
   turnaround = round(time() * 1000) - begin
   lock.acquire()
   if ('ip' not in vm or vm['ip'] == None):
      print_to_file(direc,fname, "VM" + str(total) + "\t\tFailed\t\t" + str(turnaround))
      failed += 1
   else:
      print_to_file(direc,fname, "VM" + str(total) + "\t\tSuccess\t\t" + str(turnaround))
   total += 1
   lock.release()


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
   server.publishToGroup('COMPUTE', createMessage(cmd='DESTROYALL'))
   for fname in sorted(glob.glob('*.in')):
      fp = open(fname, 'r')
      if (fname == 'random.in'):
         server.publishToHost(server.addr, createMessage(cmd="CHANGELBMODE", mode="RANDOM"), False)    
      elif (fname == 'rr.in'):
         server.publishToHost(server.addr, createMessage(cmd="CHANGELBMODE", mode="ROUNDROBIN"), False)    
      elif (fname == 'noemph.in'):
         server.publishToHost(server.addr, createMessage(cmd="CHANGELBMODE", mode="CONSOLIDATE"), False)    
      else:
         constants = ' '.join(map(lambda x: str(int(float(x)*100)),fp.read().split()))
         server.publishToHost(server.addr, createMessage(cmd="CHANGELBMODE", mode="RAIN"), False)    
         server.publishToHost(server.addr, createMessage(cmd="UPDATERAIN", constants=constants.split()), False)    
      fp.close()

      if not os.path.exists("./tests/" + fname + "/"):
         os.makedirs("./tests/" + fname + "/")

      i = 40
      while (i == 40):
         for x in range(0, 5, 1):
            total = 0
            failed = 0
            printTable(fname,"BEFORE_"+str(i)+"_"+str(x))
            threads = []
            random.seed(217645199)
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
            server.publishToGroup('COMPUTE', createMessage(cmd='DESTROYALL'))
            sleep(60)
         i -= 5

