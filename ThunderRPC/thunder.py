#!/usr/bin/env python3

'''
thunder.py
-----------------
Main THUNDER service class
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
import auth, threading, socket, socketserver, sys, platform, struct 
from interface import interface
from dictionary import *
from websocket import *
from mysql_support import mysql
from time import sleep
from config import *
from uuid import uuid1, getnode
import events as builtinEvents
from networking import *

# ensure that the address used by the service can be reused if it crashes.
socketserver.TCPServer.allow_reuse_address = True

# parse thunder config file
parseConfig('thunder.conf')

# default port of the server
SERVER_PORT = constants.get('server.port')

class ThunderRPC(threading.Thread):
    # local imports
    import rpc

    '''
    constructor ---
        Expected action:
           Sets up the object with role and group memberships
           for the local node.  Also starts the threads for
           both RPC request handlers and the multicast server
           for fault tolerance.

        Expected positional arguments:
           role - String representing the role of this node.
                  Must be either "PUBLISHER" or "SUBSCRIBER"
           group - Name of group to join as a member.  Groups
                   represent logical clusters.

        Expected return value:
           None
    '''
    def __init__(self, role = constants.get('default.role'),                   \
                 group = constants.get('default.group')):

        # invoke the constructor of the threading superclass
        super(ThunderRPC, self).__init__()

        # check the role of the service to determine the proper configuration
        if (role == 'PUBLISHER'):
            iface = constants.get('server.interface')
            port = SERVER_PORT
        elif (role == 'SUBSCRIBER'):
            iface = constants.get('default.interface')
            port = constants.get('default.port')
        else:
            print('Invalid role identifer.  Must be either ' +                  \
                  '"PUBLISHER" or "SUBSCRIBER"')
            sys.exit(-1)

        # set the interface variable, which is the interface that we want to
        # bind the service to
        self._interface = iface

        # set the role ('PUBLISHER' | 'SUBSCRIBER')
        self._role = role
 
        # set the default nonce value.  this is autogenerated, so the initial
        # value does not matter.
        self._nonce = 'DEADBEEF'

        iface_tool = interface()
        # get the IP address of the system
        self._IP = iface_tool.getAddr(iface)

        # create a TCP server, and bind it to the address of the desired
        # interface
        self._server = self.rpc.ThunderRPCServer((self._IP, port),             \
                                                 self.rpc.RequestHandler)
        self._server._ThunderRPCInstance = self
        self._server.daemon = True

        # workaround for getting the port number for auto-assigned ports
        # (default behavior for clients)
        self._port = self._server.server_address[1]

        # create a dictionary mapping an event name to a function
        self._events = Dictionary()

        # create a dictionary mapping group name to an array of tuples (IP,Port)
        # these tuples represent the clients that are connecting to this service
        # if the role of this service is SUBSCRIBER then this dictionary should
        # always be empty.
        self._clients = Dictionary()

        print('Starting ThunderRPC Service (role = %s)' % role)
        print('-------------------------------------------------')
        print('Binding to IP address - %s:%s' % (self._IP, self._port))

        # register some builtin events for metadata aggregation
        self.registerEvent('UTILIZATION', builtinEvents.utilization)
        self.registerEvent('SYSINFO', builtinEvents.sysInfo)

        # associate with a group
        self._group = group

        # give this node an arbitrary name
        self._name = getMAC(getnode())
 
        # set the default publisher to None
        self._publisher = None

        if (role == 'PUBLISHER'):
            # startup a multicasting thread to respond to multicast messages
            self.mcastThread = threading.Thread(target = self.multicastThread)
            self.mcastThread.start()
            if (self.clients.contains(self.group)): 
               c = self.clients.get(self.group)
               c.append((self.addr[0], int(self.addr[1])))
            else:
               self.clients.append((self.group, [(self.addr[0],                \
                                   int(self.addr[1]))]))
               myConnector = mysql(self.addr[0], 3306)
               myConnector.connect()
               myConnector.insertNode(self.name, self.addr[0] + ':' +          \
                                      str(self.addr[1]), self.group)
               myConnector.disconnect()
            # recreate preseeding files from template
            generatePreseed(self._IP)

        # start the thread
        self.start()

        return

    '''
    Property mutator/accessors
    '''
    # accessors and mutators
    @property
    def clients(self):
        return self._clients

    @property
    def events(self):
        return self._events

    @property
    def interface(self):
        return self._interface

    @property
    def role(self):
        return self._role

    @property
    def name(self):
        return self._name

    @property
    def addr(self):
        return (self._IP, self._port)

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, value):
        self._group = value

    @property
    def publisher(self):
        return self._publisher

    @publisher.setter
    def publisher(self, value):
        self._publisher = value

    @property
    def publisherSubnet(self):
        return self._publisherSubnet

    '''
    getClusterList() ---
        Expected action:
           Retrieves the list of clusters/groups that
           have active members.

        Expected positional arguments:
           None

        Expected return value:
           An array of cluster/group names
    '''
    def getClusterList(self):
        ret = []
        self.cleanupClients()
        for cluster in self.clients.collection():
           ret += [cluster]
        return ret

    '''
    getClientList(group) ---
        Expected action:
           Retrieves the list of clients that are member of
           a particular cluster/group

        Expected positional arguments:
           group - The name of a group

        Expected return value:
           An array of client IP/port
    '''
    def getClientList(self, group):
        listString = ''
        clist = []
        self.cleanupClients()
        for client in self.clients.get(group):
           clist += [client[0] + ':' + str(client[1])];
        return clist

    '''
    cleanupClients() ---
        Expected action:
           Checks each group for inactive clients and removes them

        Expected positional arguments:
           None

        Expected return value:
           None
    '''
    def cleanupClients(self):
        # For each group in the list of clients, find the unavailable address
        # and remove it.
        emptyGroups = []
        for grp in self.clients.collection():
            addresses = self.clients.get(grp)
            for addr in addresses:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(5)
                    s.connect(addr)
                    s.close()
                except:
                    print('Removing inactive client "%s:%d"' % (addr[0],addr[1]))
                    addresses.remove(addr)
                    myConnector = mysql(self.addr[0], 3306)
                    myConnector.connect()
                    myConnector.deleteNodeByIP(addr[0]+':'+str(addr[1]))
                    myConnector.disconnect()
                    if (len(self.clients.get(grp)) == 0):
                        emptyGroups += [grp]
        # Any groups with no clients should be removed
        for grp in emptyGroups:
            print('Removing empty group "%s"' % grp)
            del self.clients.collection()[grp]
    '''
    getMulticastingSender() ---
        Expected action:
           Sets up a socket for outbound communication over multicast

        Expected positional arguments:
           None

        Expected return value:
           The socket object
    '''
    def getMulticastingSender(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        return sock

    '''
    getMulticastingReceiver() ---
        Expected action:
           Sets up a socket for inbound communication over multicast

        Expected positional arguments:
           None

        Expected return value:
           The socket object
    '''
    # get a bound socket for receiving multicast messages
    def getMulticastingReceiver(self):
        MCAST_GRP = constants.get('default.mcastgrp')
        MCAST_PORT = constants.get('default.mcastport')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
           sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
           print('Attribute Error')
           pass

        # bind to all adapters
        sock.bind(('0.0.0.0', MCAST_PORT))
        mreq = struct.pack('4sl', socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return sock

    '''
    multicastThread() ---
        Expected action:
           Wait for requests over multicast and respond immediately.
           This is used to autoamtically locate publishers on the network.

        Expected positional arguments:
           None

        Expected return value:
           None
    '''
    def multicastThread(self):
        MCAST_GRP = constants.get('default.mcastgrp')
        MCAST_PORT = constants.get('default.mcastport')
        receiver = self.getMulticastingReceiver()
        while 1:
           try:
              data, addr = receiver.recvfrom(1024)
              msg = parseMessage(data)
              if ('cmd' in msg and msg['cmd'] == 'ROLE'):
                 # pack the role up with the client IP
                 response = createMessage(role=self.role, ip=self.addr[0])
                 receiver.sendto(response, addr)
           except:
              print('Error during multicast receive')
              pass

    '''
    findPublisher() ---
        Expected action:
           Send a request over multicast and wait for a response.
           Once the publisher is found on the network then we
           will register with that publisher as a subscriber.

        Expected positional arguments:
           None

        Expected return value:
           None
    '''
    def findPublisher(self):
        MCAST_GRP = constants.get('default.mcastgrp')
        MCAST_PORT = constants.get('default.mcastport')
        sender = self.getMulticastingSender()
        sender.settimeout(constants.get('multicast.timeout'))
        found = False
        address = None
        while(not found):
            sender.sendto(createMessage(cmd='ROLE'), (MCAST_GRP, MCAST_PORT))
            try:
                data, addr = sender.recvfrom(1024)
                response = parseMessage(data)
                if ('role' in response and response['role'] == 'PUBLISHER'):
                    address = (response['ip'],SERVER_PORT)
                    found = True
            except KeyboardInterrupt:
                raise
            except:
                print('Publisher not found, retrying.')
                continue
        self.registerClient(address, self.group)

    '''
    publishToHost() ---
        Expected action:
           Send a message to a particalur host (IP, port).
           This can be a blocking or non-blocking operation
           depending on whether the caller of this function
           expects that the response will need to timeout
           or not.

        Expected positional arguments:
           host - The (IP, port) tuple of the receiving node
           data - The message to send to the node
           timeout - Sets blocking (timeout=False) or nonblocking
                     communication.

        Expected return value:
           The response from the receiving node in the form:
           "<hostIP>:<message>"
    '''
    def publishToHost(self, host, data, timeout = True):
        retryLimit = constants.get('default.maxConnectionRetries')
        count = 0;
        while (count < retryLimit):
            try:
                # open a socket connection
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if (timeout):
                    s.settimeout(constants.get('default.messageTimeout'))
                else:
                    s.settimeout(None)
                s.connect(host)
                # encode the data before sending
                s.send(data)
                # wait for a response from the host
                response = s.recv(1024).decode().strip()
                s.close()
                # return a colon delimited string containing the IP address of
                # the host and its response
                if (response == ''):
                   ret = {}
                else:
                   ret = parseMessage(response)
                ret['_HOST_'] = host
                return ret
            except:
                print('Host', host[0] + ':' + str(host[1]),                    \
                      'didn\'t respond.  Trying again.')
            count += 1
        raise Exception("Timeout")

    '''
    publishToGroup() ---
        Expected action:
           Send a message to a particalur group/cluster.
           This can be a blocking or non-blocking operation
           depending on whether the caller of this function
           expects that the response will need to timeout
           or not.

        Expected positional arguments:
           group - The name of the group to send the message to
           data - The message to send to the group
           timeout - Sets blocking (timeout=False) or nonblocking
                     communication.

        Expected return value:
           The responses from the nodes in the group separated 
           by semicolons or None if nothing is returned.
    '''
    def publishToGroup(self, group, data, timeout = False):
        ret = []
        if (self.clients.contains(group)):
            addresses = self.clients.get(group)
            for addr in addresses:
                try:
                    val = self.publishToHost(addr, data, timeout)
                    if (val != None):
                         ret += [val]
                except:
                   print("Timeout in communicating with", addr)
        return ret

    '''
    registerEvent() ---
        Expected action:
           Register an event by adding a mapping between logical name
           and function to a global dictionary of events.

        Expected positional arguments:
           name - The name of the event 
           event - The function being mapped to 

        Expected return value:
           None
    '''
    def registerEvent(self, name, event):
        print('Registering event - "%s (%s)"' % (name, event.__name__))
        self.events.append((name, event))

    '''
    registerClient() ---
        Expected action:
           Registers a node (IP, port) with a particular publisher
           and assigns group membership of the node.

        Expected positional arguments:
           host - The (IP, port) tuple of the subscriber
           group - The group that the subscriber is joining

        Expected return value:
           None
    '''
    def registerClient(self, host, group):
        # send an authorization request to the server.  The server should
        # return a nonce value.
        ret = self.publishToHost(host, createMessage(cmd='AUTH'))
        nonce = ret['nonce']

        # encrypt the nonce with pre-shared key and send it back to the host.
        decVal = auth.encrypt(nonce).decode('UTF8')

        message = createMessage(cmd='SUBSCRIBE',
                                ip=self.addr[0],
                                port=self.addr[1],
                                group=self.group,
                                nonce=decVal)

        # TODO: What to do with ret?
        ret = self.publishToHost(host, message) 

        # save the IP of the publisher.
        self._publisher = host

        # start a heartbeat for fault tolerance
        self._heartBeatThread = threading.Thread(target = self.heartBeat)
        self._heartBeatThread.start()

        # Insert the ndoe into the database
        myConnector = mysql(str(host[0]), 3306)
        myConnector.connect()
        myConnector.insertNode(self.name, self.addr[0]+':'+str(self.addr[1]), self.group)
        myConnector.disconnect()

    '''
    heartbeat() ---
        Expected action:
           Thread that periodically will send out a heartbeat
           request to the publisher to make sure that it is
           still alive.  If the publisher does not respond then
           the node will attempt to reconnect to another publisher
           on the network.

        Expected positional arguments:
           None

        Expected return value:
           None
    '''
    def heartBeat(self):
        # if there is no publisher to ping then something bad happened.
        if (self._publisher == None):
            self.findPublisher()
            return

        message = createMessage(cmd='HEARTBEAT', ip=self.addr[0], port=self.addr[1])
        alive = True
        while (alive):
            sleep(constants.get('heartbeat.interval'))
            
            try:
               ret = self.publishToHost(self._publisher, message)
            except:
               continue
            if (ret == None):
                alive = False
            else:
                if (ret['result'] == 'SUBSCRIBE'):
                    alive = False
        self.findPublisher()
        return

    '''
    run() --- inherited from threading.Thread
        Expected action:
           Continuously handle requests coming in over the
           socket server.

        Expected positional arguments:
           None

        Expected return value:
           None
    '''
    def run(self):
        self.running = True
        self._server.serve_forever()
        self._server.shutdown()
        return
