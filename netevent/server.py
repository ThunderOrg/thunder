#! /usr/bin/env python3

# server component of Thunder Cloud
# Copyright 2014 Gabriel Jacob Loewen

from NetEvent import *

# Invoke a function and return the result.
def invoke(params):
   if (len(params) > 1):
      if (params[0] == "CONTROL"):
         if (params[1] == "GET_CLIENT_LIST"):
            return netEvent.getClientList()
         elif (params[1] == "GET_CLUSTER_LIST"):
            return netEvent.getClusterList()
      elif (params[0] == "GROUP"):
         return netEvent.publishToGroup(params[2], params[1])
      elif (params[0] == "HOST"):
         host = (params[1], int(params[2]))
         return netEvent.publishToHost(host,params[3])
   # Invalid number of params.  Return error code.
   else:
      return -1

# Instantiate NetEvent and register the invoke event
netEvent = NetEvent(49687, 'eth0', 'ADMIN')
netEvent.registerEvent("INVOKE", invoke)
