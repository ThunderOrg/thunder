#!/usr/bin/env python3

'''
config.py
-----------------
Module for parsing the Thunder configuration file
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

# Imports
from dictionary import *
import sys
import builtins

# Create a dictionary to store results
builtins.constants = Dictionary()

'''
parseConfig(fname) ---
    Expected action:
        Read the file, parse the configuration, and store
        the data in a dictionary of key-value mappings

    Expected positional arguments:
        fname - Filename of configuration file

    Expected return value:
        None
'''
def parseConfig(fname):
    fp = open(fname, 'r')
    lines = fp.readlines()
    for line in lines:
        # remove any leading or ending spaces
        line = line.strip()
        if (line != '' and line[0] != '#'):
            keyval = line.split('&')
            key = keyval[0].strip()
            val = keyval[1].strip()
            cIndex = len(val)
            # remove any ending comments
            for i in range(0, len(val), 1):
                ch = val[i]
                if (ch == '#'):
                    cIndex = i
                    break
            val = val[:cIndex].strip()
            if (val[0] == '"' and val[-1] == '"'):
                val = val[1:-1]
            else:
                try:
                   val = int(val)
                except:
                   print('Could not parse config on line:\n\t' + line)
                   sys.exit(-1)
            constants.append([key,val])
    fp.close()
