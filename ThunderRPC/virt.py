import sys, tarfile, uuid

def connect():
   conn = libvirt.open('qemu:///system')
   if (conn == None):
      print 'Failed to open connection to hypervisor'
      sys.exit(-1)

   return conn

def mountVMPool(conn, hostname, sharename):
   try:
      vmpool = conn.storagePoolLookupByName(sharename)
      if (vmpool.isActive()):
         vmpool.destroy()
      vmpool.undefine()
   except libvirt.libvirtError as err:
      print err

   target = "/thunderImg/" + sharename
   createTarget(target)

   vmpool = conn.storagePoolDefineXML(getImagePoolSpec(hostname,sharename,target),0)
   vmpool.setAutostart(True)
   ret = vmpool.create(0)

   # The storage pool was created.
   if (ret==0):
      return vmpool, target
   else:
      sys.exit(-1)

def getImageList(directory):
   specList = []
   dirList = os.listdir(directory)
   for item in dirList:
      if (path.isfile(item) and item.endswidth(".spec")):
         specList += [item]

   # speclist contains all specification files.
   return specList

def instantiate(conn, domain):
   try:
      domain = conn.lookupByName(domain)
   except:
      print "Failed to find the domain: %s" % (domain)
      sys.exit(1)

   domain.create()

def getImagePoolSpec(host,dir_path,target_path):
   # Setup image pool XML specification
   image_pool_xml = """   <pool type=\"netfs\">
     <name>""" + dir_path + """</name>
     <source>
       <host name=\"""" + host + """\"/>
       <dir path=\"""" + dir_path + """\"/>
       <format type='cifs'/>
     </source>
     <target>
       <path>""" + target_path + """</path>
     </target>
   </pool>"""
   return image_pool_xml

def createTarget(path):
   try:
      os.makedirs(path)
   except OSError as exception:
      if exception.errno != errno.EEXIST:
         raise

def setup(target):
   path = "/var/lib/libvirt/images/"
   tar = tarfile.open(target, 'r')
   # install the image in libvirt

#requestID = sys.argv[1]
#location = sys.argv[2]
#vmname = sys.argv[3]
#conn = connect()

#pool, target = mountVMPool(conn, location, "ThunderImages")
#specs = getImageList(target)

#if (domain+'.spec' in specs):
   # Copy tarball of domain into /var/lib/libvirt/images and unpack
   # into a unique directory. Then install the domain into libvirt.
#   setup(target + "/" + domain + ".tgz")

#instantiate(conn, domain)
print "hello"
