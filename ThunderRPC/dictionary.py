#!/usr/bin/env python3

'''
dictionary.py
-----------------
Dictionary wrapper with additional functions
Developed by Gabriel Jacob Loewen
The University of Alabama
Cloud and Cluster Computing Group
'''

class Dictionary:
   # Constructor
   def __init__(self):
      self.dict = {}

   # Append key/value pair to dictionary
   def append(self, keyval):
      self.dict[keyval[0]] = keyval[1]

   # Remove a key from the dicionary
   def remove(self, key):
      del self.dict[key]

   # Removes all data from dictionary
   def clear(self):
      self.dict.clear()
      del self.dict
      self.dict = {}

   # Retrieves a value from a key/value pair
   def get(self, key):
      return self.dict[key]

   # Returns True if the dictionary contains the specified key
   def contains(self, key):
      return key in self.dict

   # Returns the length of the dictionary
   def length(self):
      return len(self.dict)

   # Returns the raw Python dictionary collection
   def collection(self):
      return self.dict
