#! /usr/bin/env python3

# Cloud Controller (Zeus) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

from thunder import *
import sys

# Invoke a function and return the result.
def invoke(*params):
   tag = params[0]
   data = params[1]

   if (len(data) > 1):
      if (data[0] == "CONTROL"):
         if (data[1] == "GET_CLIENT_LIST"):
            return server.getClientList()
         elif (data[1] == "GET_CLUSTER_LIST"):
            return server.getClusterList()
      elif (data[0] == "GROUP"):
         return server.publishToGroup(params[2], params[1])
      elif (data[0] == "HOST"):
         host = (params[1], int(params[2]))
         return server.publishToHost(host,params[3])
   # Invalid number of params.  Return error code.
   else:
      return None

# Instantiate NetEvent and register the invoke event
server = ThunderRPC(role = 'PUBLISHER', group = 'Cloud')
server.registerEvent('INVOKE', invoke)

if (len(sys.argv) > 1 and sys.argv[1] == 'console'):
   print("THUNDER Console")
   group = ''
   data = ''
   done = False
   while (not done):
      group = input("group> ")
      data = input("data> ")
      result = server.publishToGroup(group, data)
      print(result)
      done = eval(input("done? "))
   print("finished")
