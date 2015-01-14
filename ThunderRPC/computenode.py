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
   nas = myConnector.getNASAddress(serverName)[0].split(':')[0]
   domain = str(uuid1()).replace('-','')
   myConnector.insertInstance(domain, "-1", client.name, username, name)
   myConnector.disconnect()

   # transfer the archive over
   archive = image['archive']
   copyFromNAS(archive, domain, nas)

   # collect data about the archive contents
   disk = image['disk']
   overlay = image['overlay']
   config = image['config']
   ram = profile['ram']
   vcpus = profile['vcpus']
   dest_dir = constants.get("default.imagedir")

   # clone the image and install into virsh
   virtHelper = subprocess.Popen(['./cloneAndInstall.sh', archive, domain, disk, overlay, config, ram, vcpus, dest_dir], stdout=subprocess.PIPE)
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

def copyFromNAS(imageName, name, server):
   # Create a temp file for the image
   opener = urllib.request.build_opener(SMBHandler) 
   src = opener.open("smb://"+server+"/share/images/"+imageName)

   # Save the image to the correct location
   dest_dir = constants.get("default.imagedir")

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
