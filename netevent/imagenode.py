#!/usr/bin/env python3
from NetEvent import *

def main():
   netEvent = NetEvent()
   netEvent.associateGroup("IMAGES")
   netEvent.findController()

main()
