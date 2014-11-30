from config import *

VCORES_PERCORE = int(constants.get('default.vcoresPerCore'))

def select(nodes, weights, vm):
   rankings = getRankings(nodes, weights)
   rankings.sort(key=lambda tup: tup[1])
   for rank in rankings:
      if (fits(rank[0], vm)):
         return rank[0]
   return None

def getRankings(nodes, weights):
   vec = []
   for node in reversed(nodes):
      nodeArr = node.split(':')
      vec += [[nodeArr, rank(nodeArr[1:], weights)]]
   return vec
      
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

def fits(node, vm):
   freeVCores = int(node[6]) - int(node[7])
   freeRam = int(node[2])
   if (freeVCores >= int(vm['vcpus']) and freeRam >= int(vm['ram'])):
      return 1
   return 0
