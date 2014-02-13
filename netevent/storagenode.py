#!/usr/bin/env python3
from NetEvent import *

def main():
   netEvent = NetEvent()
   netEvent.associateGroup("PRIMARY_STORAGE")
   netEvent.registerEvent("GETIMAGESINFO", getImagesInfo)
   netEvent.findController()

def getImagesInfo(params):
    return 0

main()
