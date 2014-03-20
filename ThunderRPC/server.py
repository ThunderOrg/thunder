#! /usr/bin/env python3

# server component of Thunder Cloud
# Copyright 2014 Gabriel Jacob Loewen

from ThunderRPC import *

# Invoke a function and return the result.
def invoke(params):
   if (len(params) > 1):
      if (params[0] == "CONTROL"):
         if (params[1] == "GET_CLIENT_LIST"):
            return server.getClientList()
         elif (params[1] == "GET_CLUSTER_LIST"):
            return server.getClusterList()
      elif (params[0] == "GROUP"):
         return server.publishToGroup(params[2], params[1])
      elif (params[0] == "HOST"):
         host = (params[1], int(params[2]))
         return server.publishToHost(host,params[3])
   # Invalid number of params.  Return error code.
   else:
      return -1

# Instantiate NetEvent and register the invoke event
server = ThunderRPC(role = 'PUBLISHER', group = "Cloud")
server.registerEvent("INVOKE", invoke)
