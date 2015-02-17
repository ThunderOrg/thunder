#!/usr/bin/env python3

'''
storagenode.py
-----------------
Storage Controller (Indra) component of Thunder
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
import subprocess
from thunder import *
from message import createMessage

def importImage(*params):
   args = params[1]
   url = args[0]
   imageDir = constants.get('default.imagedir')
   # Download the image from the url
   p = subprocess.Popen(['./getImage.sh', url, imageDir], stdout=subprocess.PIPE)
   out,err=p.communicate()
   if (err != ''):
      return createMessage(result=1)
   print(out)
   # Untar the image
   
   # Put the data from the YAML into the database
   # Store the image tar in the share
   return createMessage(result=0)

client = ThunderRPC(group = 'STORAGE')
client.registerEvent('IMPORTIMAGE', importImage)
client.findPublisher()
