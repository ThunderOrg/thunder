#!/usr/bin/env python3

# Compute Controller (Thor) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import tempfile, libvirt, urllib.request, shutil, os, subprocess
from mysql_support import mysql
from thunder import *
from smb.SMBHandler import SMBHandler
from uuid import uuid1
from time import sleep

def instantiate(*params):
   print("IN INSTANTIATE")
   args = params[1]
   name = args[0]
   username = args[1]

   publisher = client.publisher[0]

   myConnector = mysql(publisher, 3306)
   myConnector.connect()
   profile = myConnector.getProfileData(name)
   image = myConnector.getImageData(profile['image'])
   serverName = image['node']

   # Lookup name in database to find network location of image
   nas = myConnector.getNASAddress(serverName)[0].split(':')[0]
   domain = str(uuid1()).replace('-','')
   myConnector.insertInstance(domain, "-1", client.name, username, name)
   myConnector.disconnect()

   diskPath = domain + ".img"
   configPath = domain + ".config"

   copyFromNAS(image['disk'], image['directory'], diskPath, nas)
   copyFromNAS(image['config'], image['directory'], configPath, nas)

   virtHelper = subprocess.Popen(['./cloneAndInstall.sh', diskPath, configPath, domain], stdout=subprocess.PIPE)
   out, err = virtHelper.communicate()
   mac = out.decode().rstrip().replace(':','-')
   return mac + ':' + domain

def destroy(*params):
   args = params[1]
   domain = args[0]
   vmDestructor = subprocess.Popen(['./destroyVM.sh', domain], stdout=subprocess.PIPE)
   vmDestructor.communicate()
   publisher = client.publisher[0]
   myConnector = mysql(publisher, 3306)
   myConnector.connect()
   myConnector.deleteInstance(domain)
   myConnector.disconnect()
   return 'success'

def copyFromNAS(imageName, directory, name, server):
   # Create a temp file for the image
   opener = urllib.request.build_opener(SMBHandler) 
   print(server)
   print(directory)
   print(imageName)
   src = opener.open("smb://"+server+"/share/images/"+directory+"/"+imageName)

   # Save the image to the correct location
   dest_dir = "/srv/images"

   fname = dest_dir + "/" + name

   dest = open(fname, "wb")
   shutil.copyfileobj(src,dest)

   # Close files
   src.close()
   dest.close()

client = ThunderRPC()
client.registerEvent("INSTANTIATE", instantiate)
client.registerEvent("DESTROY", destroy)
client.findPublisher()
