#! /usr/bin/env python3
from NetEvent import *

def invoke(params):
   if (len(params) < 3):
      return '-1'
   else:
      if (params[0] == "CONTROL"):
         if (params[1] == "GET_CLIENT_LIST"):
            return netEvent.getClientList()
         elif (params[1] == "GET_CLUSTER_LIST"):
            return netEvent.getClusterList()
      elif (params[0] == "GROUP"):
         return netEvent.publishToGroup(params[1], params[2])
      elif (params[0] == "HOST"):
         host = (params[1], int(params[2]))
         return netEvent.publishToHost(host,params[3])

netEvent = NetEvent(6667, "ADMIN")
netEvent.registerEvent("INVOKE", invoke)
