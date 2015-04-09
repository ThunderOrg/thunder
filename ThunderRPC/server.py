#!/usr/bin/env python3

'''
server.py
-----------------
Cloud Controller (Zeus) component of Thunder
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
from thunder import *

server = ThunderRPC(role = 'PUBLISHER', group = 'CONTROLLER')
