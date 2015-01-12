#!/usr/bin/env python3

# Storage Controller (Indra) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

from thunder import *

def importImage(*params):
   args = params[1]
   print(args)
   return 'success'

client = ThunderRPC(group = 'STORAGE')
client.registerEvent("IMPORTIMAGE", importImage)
client.findPublisher()
