#! /usr/bin/env python3
from NetEvent2 import *

def invoke(params):
   if (len(params) < 2):
      return '-1'
   else:
      if (params[0] == "CONTROL"):
         print("CONTROL")
         if (params[1] == "GET_CLIENT_LIST"):
            return netEvent.getClientList()
         elif (params[1] == "GET_CLUSTER_LIST"):
            print(netEvent.getClusterList())
            return netEvent.getClusterList()
      elif (params[0] == "GROUP"):
         return netEvent.publishToGroup(params[2], params[1])
      elif (params[0] == "HOST"):
         host = (params[1], int(params[2]))
         return netEvent.publishToHost(host,params[3])

netEvent = NetEvent(6667, 'eth0', 'ADMIN')
netEvent.registerEvent("INVOKE", invoke)
