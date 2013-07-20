import libvirt
import sys

def connect():
   conn = libvirt.open('qemu:///system')
   if (conn == None):
      print 'Failed to open connection to hypervisor'
      sys.exit(-1)

   return conn

def mountVMPool(conn, hostname, sharename = "virtimages"):
   try:
      vmpool = conn.storagePoolLookupByName("virtimages")
      if (vmpool.isActive()):
         vmpool.destroy()
      vmpool.undefine()
   except libvirt.libvirtError as err:
      print err

   vmpool = conn.storagePoolDefineXML(getImagePoolSpec(hostname,sharename,"/var/lib/libvirt/images/"),0)
   vmpool.setAutostart(True)
   ret = vmpool.create(0)
   print ret
   if (ret==0):
      return vmpool
   else:
      sys.exit(-1)

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
     <name>virtimages</name>
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

conn = connect()
pool = mountVMPool(conn, sys.argv[1], sys.argv[2])
instantiate(conn, sys.argv[3])
