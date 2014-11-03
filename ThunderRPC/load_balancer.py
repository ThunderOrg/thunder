from config import *

VM_MAX = int(constants.get('default.vcoresPerCore'))

def select(nodes, weights, vm):
   rankings = getRankings(nodes, weights)
   rankings.sort(key=lambda tup: tup[1])
   #for rank in rankings:
      
   return 0

def getRankings(nodes, weights, vmMax):
   vec = []
   for node in reversed(nodes):
      vec.push([node, rank(node, weights, vmMax)])
   return vec
      
def rank(node, weights):
   # RAM
   memTotal = node[0]
   memFree = node[1]
   memUsed = memTotal - memFree
   loadOne = node[2]
   loadFive = node[3]
   loadFifteen = node[4]
   activeVMs = node[5]
   numCores = node[6]
   
   sRAM = weights[0] * (memUsed / memTotal)
   sLoad1 = weights[1] * (loadOne / numCores)
   sLoad5 = weights[2] * (loadFive / numCores)
   sLoad15 = weights[3] * (loadFifteen / numCores)
   sActiveVMs = weights[4] * (activeVMs / (numCores * vmMax))

   return sRAM + sLoad1 + sLoad5 + sLoad15 + sActiveVMs

#def fits(node, vm):
   
