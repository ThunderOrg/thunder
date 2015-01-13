#!/usr/bin/env python3

# Storage Controller (Indra) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import subprocess
from thunder import *

def importImage(*params):
   args = params[1]
   url = args[0]
   # Download the image from the url
   p = subprocess.Popen('wget -U firefox ' + url, shell=True) 
   print(p.wait())
   # Untar the image
   # Put the data from the YAML into the database
   # Store the image tar in the share
   return 'success'

client = ThunderRPC(group = 'STORAGE')
client.registerEvent("IMPORTIMAGE", importImage)
client.findPublisher()
