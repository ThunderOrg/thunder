#!/usr/bin/env python3

# Compute Controller (Thor) component of Thunder
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

from thunder import *
import tempfile
import libvirt
import mysql_support
from smb.SMBHandler import SMBHandler
import urllib.request
import shutil
from uuid import uuid1
import os
from xml.etree import ElementTree
import subprocess
from time import sleep

def main():
   client = ThunderRPC()
   client.registerEvent("INSTANTIATE", instantiate)
   client.registerEvent("DESTROY", destroy)
   client.findPublisher()
   instantiate("ubuntu")

def instantiate(*params):
   name = params[0]

   # open connection to hypervisor
   conn = libvirt.openReadOnly(None)
   if conn == None:
      return -1

   image = mysql_support.getImageData(name)
   serverName = image['node']

   # Lookup name in database to find network location of image
   nas = mysql_support.getNASAddress(serverName)[0]
   
   copyFromNAS(image['name'], name + '.' + image['type'], nas)
   copyFromNAS('configuration.iso', 'configuration.iso', nas)

   domain = str(uuid1()).replace('-','')

   virtHelper = subprocess.Popen(['./cloneAndInstall.sh', str(name + '.' + image['type']), domain], stdout=subprocess.PIPE)
   out, err = virtHelper.communicate()
   ip = out.decode().rstrip()
   mysql_support.insertInstance(domain, ip)

   return domain, ip 

def destroy(*params):
   subprocess.Popen(['./destroyVM.sh', domain], stdout=subprocess.PIPE)
   mysql_support.deleteInstance(domain)
   
def copyFromNAS(imageName, name, server):
   # Create a temp file for the image
   opener = urllib.request.build_opener(SMBHandler) 
   src = opener.open("smb://"+server+"/share/images/"+imageName)

   # Save the image to the correct location
   dest_dir = "/var/lib/libvirt/images/"
   if not os.path.exists(dest_dir):
      os.makedirs(dest_dir)
   fname = dest_dir + "/"+name
   if os.path.isfile(fname):
      os.remove(fname)
   dest = open(fname, "wb")
   shutil.copyfileobj(src,dest)

   # Close files
   src.close()
   dest.close()

main()
