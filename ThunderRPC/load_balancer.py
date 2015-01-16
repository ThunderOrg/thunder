#!/usr/bin/env python3

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

'''
select(nodes, weights, vm) ---
    Expected action:
        Select a node to instantiate using RAIN

    Expected positional arguments:
        nodes - array of node metadata
        weights - array of RAIN weights selected by user
        vm - virtual machine descriptor (RAM, #cores, etc,)

    Expected return value:
        The selected node descriptor if one is suitable, None otherwise
'''
def select(nodes, weights, vm):
   rankings = getRankings(nodes, weights)
   sortedRankings = sorted(rankings, key=lambda rank: rank[1])
   for rank in sortedRankings:
      if (fits(rank[0], vm)):
         return rank[0]
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
      nodeArr = node.split(':')
      vec.append((nodeArr, rank(nodeArr[1:], weights)))
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
   freeVCores = int(node[6]) - int(node[7])
   freeRam = int(node[2])
   if (freeVCores >= int(vm['vcpus']) and freeRam >= int(vm['ram'])):
      return True
   return False
