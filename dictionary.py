class Dictionary:
   def __init__(self):
      self.dict = {}

   def append(self, keyval):
      self.dict[keyval[0]] = keyval[1]

   def remove(self, key):
      del self.dict[key]

   def clear(self):
      self.dict.clear()
      del self.dict
      self.dict = {}

   def get(self, key):
      return self.dict[key]

   def contains(self, key):
      return key in self.dict

   def length(self):
      return len(self.dict)

   def collection(self):
      return self.dict
