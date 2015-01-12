#!/usr/bin/env python3

# Storage Controller (Indra) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

from thunder import *

def importImage(*params):
   url = params[1]
   # Download the image from the url
   # Untar the image
   # Put the data from the YAML into the database
   # Store the image tar in the share
   return 'success'

client = ThunderRPC(group = 'STORAGE')
client.registerEvent("IMPORTIMAGE", importImage)
client.findPublisher()
