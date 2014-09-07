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
   nas = myConnector.getNASAddress(serverName)[0]
  
   domain = str(uuid1()).replace('-','')
   diskPath = domain + ".img"
   configPath = domain + ".config"

   copyFromNAS(image['disk'], image['directory'], diskPath, nas)
   copyFromNAS(image['config'], image['directory'], configPath, nas)

   virtHelper = subprocess.Popen(['./cloneAndInstall.sh', diskPath, configPath, domain], stdout=subprocess.PIPE)
   out, err = virtHelper.communicate()
   ip = out.decode().rstrip()

   myConnector.insertInstance(domain, ip, client.name, username, name)
   myConnector.disconnect()
   return "success"

def destroy(*params):
   args = params[1]
   domain = args[0]
   subprocess.Popen(['./destroyVM.sh', domain], stdout=subprocess.PIPE)
   myConnector = mysql(publisher, 3306)
   myConnector.connect()
   myConnector.deleteInstance(domain)
   myConnector.disconnect()

def copyFromNAS(imageName, directory, name, server):
   # Create a temp file for the image
   opener = urllib.request.build_opener(SMBHandler) 
   src = opener.open("smb://"+server+"/share/images/"+directory+"/"+imageName)

   # Save the image to the correct location
   dest_dir = "/var/lib/libvirt/images"

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
