#!/usr/bin/env python3

'''
computenode.py
-----------------
Compute Controller (Thor) component of THUNDER
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
import tempfile, urllib.request, shutil, os, subprocess
from mysql_support import mysql
from thunder import *
from smb.SMBHandler import SMBHandler
from uuid import uuid1
from time import sleep
from message import createMessage

'''
instantiate(*params) ---
    Expected action:
        This function should copy the virtual machine image
        from the storage node, unpack the image, generate
        a unique domain name, and instantiate it.

    Expected positional arguments:
        args[0] - Virtual machine name
        args[1] - Username of requester

    Expected return value:
        MAC Aaddress of virtual machine instance with colonds replaced with 
        dashesand and the domain name in the format: "<MAC>:<DOMAIN>"
'''
def instantiate(data):
   # Get posiotional arguments
   name = data['vm']
   username = data['user']

   # Get the IP of the publisher
   publisher = client.publisher[0]

   # Get image information
   myConnector = mysql(publisher, 3306)
   myConnector.connect()
   profile = myConnector.getProfileData(name)
   image = myConnector.getImageData(profile['image'])
   serverName = image['node']

   # Lookup name in database to find network location of image
   nas = myConnector.getNASAddress(serverName)[0].split(':')[0]
   domain = str(uuid1()).replace('-','')
   myConnector.insertInstance(domain, '-1', client.name, username, name)
   myConnector.disconnect()

   # transfer the archive over
   archive = image['archive']
   copyFromNAS(archive, archive, nas)

   # collect data about the archive contents
   disk = image['disk']
   overlay = image['overlay']
   config = image['config']
   ram = str(profile['ram'])
   vcpus = str(profile['vcpus'])
   dest_dir = constants.get('default.imagedir')+"/"+domain

   # clone the image and install into virsh
   virtHelper = subprocess.Popen(['./cloneAndInstall.sh', archive, domain,     \
                                  disk, overlay, config, ram, vcpus,           \
                                  dest_dir], stdout=subprocess.PIPE,           \
                                  stderr=subprocess.PIPE)
   out, err = virtHelper.communicate()
   print(out)
   print(err)
   mac = out.decode().rstrip().replace(':','-')
   result = {}
   result['mac'] = mac
   result['domain'] = domain
   return result

'''
destroy(*params) ---
    Expected action:
        This function should stop and destroy a running
        virtual machine

    Expected positional arguments:
        args[0] - Domain name of running virtual machine instance

    Expected return value:
        0 - successful
        1 - unsuccessful
'''
def destroy(data):
   domain = data['domain']
   vmDestructor = subprocess.Popen(['./destroyVM.sh', domain],                 \
                                   stdout=subprocess.PIPE)
   out, err = vmDestructor.communicate()
   if (err != ""):
      return 1
   publisher = client.publisher[0]
   myConnector = mysql(publisher, 3306)
   myConnector.connect()
   myConnector.deleteInstance(domain)
   myConnector.disconnect()
   return 0

'''
destroyAll(*params) ---
    Expected action:
        This function should stop and destroy all running
        virtual machine

    Expected positional arguments:
        None

    Expected return value:
        0 - successful
        1 - unsuccessful
'''
def destroyAll(data):
   vmDestructor = subprocess.Popen('./destroyAll.sh',                          \
                                   stdout=subprocess.PIPE)
   out, err = vmDestructor.communicate()
   if (err != ""):
      return 1
   publisher = client.publisher[0]
   myConnector = mysql(publisher, 3306)
   myConnector.connect()
   myConnector.deleteInstance(domain)
   myConnector.disconnect()
   return 0

'''
copyFromNAS(imageName, name, server) ---
    Expected action:
        This function should copy a file from the storage node
        to the local images directory

    Expected positional arguments:
        imageName - Name of the archive to copy (ex: ubuntu.tar.xz)
        name - Name to save the image as locally (ex: myimage.tar.xz)
        server - IP and port of storage node to copy data from                 \
                 (ex: (10.10.0.1:48574))

    Expected return value:
        0 - successful
        1 - unsuccessful
'''
def copyFromNAS(imageName, name, server):
   # Create a temp file for the image
   opener = urllib.request.build_opener(SMBHandler) 
   src = opener.open('smb://' + server + '/share/images/' + imageName)

   # Save the image to the correct location
   dest_dir = constants.get('default.imagedir')

   fname = dest_dir + '/' + name

   dest = open(fname, 'wb')
   shutil.copyfileobj(src,dest)

   # Close files
   src.close()
   dest.close()

# Start up the service and register events
client = ThunderRPC()
client.registerEvent('INSTANTIATE', instantiate)
client.registerEvent('DESTROY', destroy)
client.registerEvent('DESTROYALL', destroyAll)
client.findPublisher()
