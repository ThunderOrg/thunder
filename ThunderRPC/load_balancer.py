#!/usr/bin/env python3
import random
import threading

'''
load_balancer.py
-----------------
RAIN implementation and generic load balancing functions
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Get the default number of vcores allocated per physical core
VCORES_PERCORE = constants.get('default.vcoresPerCore')
rr_index=0
rr_lock = threading.Lock()

'''
rain_select(nodes, weights, vm) ---
    Expected action:
        Select a node to instantiate using RAIN

    Expected positional arguments:
        nodes - array of node metadata
        weights - array of RAIN weights selected by user
        vm - virtual machine descriptor (RAM, #cores, etc,)

    Expected return value:
        The selected node descriptor if one is suitable, None otherwise
'''
def rain_select(nodes, weights, vm):
   rankings = getRankings(nodes, weights)
   sortedRankings = sorted(rankings, key=lambda rank: rank[2])
   for rank in sortedRankings:
      if (fits(rank[0], vm)):
         return rank[1]
   return None

'''
getRankings(nodes, weights) ---
    Expected action:
        Rank each node using RAIN algorithm 

    Expected positional arguments:
        nodes - array of node metadata
        weights - array of RAIN weights selected by user

    Expected return value:
        Vector of nodes and corresponding ranks
'''
def getRankings(nodes, weights):
   vec = []
   for node in reversed(nodes):
      nodeArr = node['result']
      vec.append((nodeArr, node['_HOST_'], rank(nodeArr, weights)))
   return vec

'''
rank(node, weights) ---
    Expected action:
        Rank one node using RAIN algorithm 

    Expected positional arguments:
        node - node metadata
        weights - array of RAIN weights selected by user

    Expected return value:
        Real number rank of one node
'''
def rank(node, weights):
   # RAM
   memTotal = int(node[0])
   memFree = int(node[1])
   memUsed = memTotal - memFree

   # Load
   loadOne = float(node[2])
   loadFive = float(node[3])
   loadFifteen = float(node[4])
   
   # VCores
   maxVCores = int(node[5])
   activeVCores = int(node[6])
  
   # Get the actual number of cores
   numCores = maxVCores / VCORES_PERCORE 
 
   # Calculate terms of rank
   sRAM = weights[0] * (memUsed / memTotal)
   sLoad1 = weights[1] * (loadOne / numCores)
   sLoad5 = weights[2] * (loadFive / numCores)
   sLoad15 = weights[3] * (loadFifteen / numCores)
   sActiveVMs = weights[4] * (activeVCores / maxVCores)

   return sRAM + sLoad1 + sLoad5 + sLoad15 + sActiveVMs

'''
fits(node, vm) ---
    Expected action:
        Checks if a virtual machine can fit on a node

    Expected positional arguments:
        node - node metadata
        vm - virtual machine descriptor (RAM, #cores, etc,)

    Expected return value:
        True or False
'''
def fits(node, vm):
   print("NODE:", node)
   freeVCores = int(node[5]) - int(node[6])
   freeRam = int(node[1])
   if (freeVCores >= int(vm['vcpus']) and freeRam >= int(vm['ram'])):
      return True
   return False

'''
rr_reset() ---
    Expected action:
        Resets the node array index for round robin

    Expected positional arguments:
        None

    Expected return value:
        None
'''
def rr_reset():
   global rr_index
   rr_lock.acquire()
   rr_index=0
   rr_lock.release()

'''
rr_select() ---
    Expected action:
        Selects a node using round robin

    Expected positional arguments:
        nodes - array of node metadata
        vm - virtual machine descriptor (RAM, #cores, etc,)

    Expected return value:
        The node, if one exists.  None otherwise.
'''
def rr_select(nodes, vm):
   global rr_index
   orig_index = rr_index
   retval = None
   touched = 0
   while (touched < len(nodes)):
      if (rr_index > len(nodes)-1):
         rr_reset()

      rr_lock.acquire()
      node = nodes[rr_index]
      rr_lock.release()
      touched += 1

      if (fits(node['result'], vm)):
         retval = node['_HOST_']
         break
      rr_lock.acquire()
      rr_index += 1
      rr_lock.release()
   rr_lock.acquire()
   rr_index += 1
   rr_lock.release()
   return retval

'''
rand_select() ---
    Expected action:
        Selects a random node

    Expected positional arguments:
        nodes - array of node metadata
        vm - virtual machine descriptor (RAM, #cores, etc,)

    Expected return value:
        The node, if one exists.  None otherwise.
'''
def rand_select(nodes, vm):
   r = random.randrange(0, len(nodes), 1)
   node = nodes[r]['result']
   if (fits(node, vm)):
      return nodes[r]['_HOST_']
   else:
      return None
