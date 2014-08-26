# Dictionary wrapper with additional functions
# Written by Gabriel Jacob Loewen
# Copyright 2013 Gabriel Jacob Loewen

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
