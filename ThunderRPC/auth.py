# A component of the ThunderRPC that dealds with node authentication.
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Lab
# Copyright 2014 Gabriel Jacob Loewen

import base64
from Crypto import Random
from Crypto.Random import random
from Crypto.Cipher import AES

# Shared key!  This should probably be more secure...
k = b'YM{<GC\xdaQ\x80\xe8\xd8\xcf\xf1\xf7\xdaM'

# Blocksize for crypto and padding to make sure the length is as expected
BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(chr(s[-1]))]

# generateNonce - Generates a random 32-bit value
def generateNonce():
   return str(random.getrandbits(32))

# encrypt - Encrypts the raw data passed into the function using AES
def encrypt(raw):
   raw = pad(raw)
   iv = Random.new().read( AES.block_size )
   cipher = AES.new( k, AES.MODE_CBC, iv )
   return base64.b64encode( iv + cipher.encrypt( raw ) ) 

# decrypt - Decrypts the encrypted data using the shared key
def decrypt(enc):
   enc = base64.b64decode(enc)
   iv = enc[:16]
   cipher = AES.new(k, AES.MODE_CBC, iv)
   return unpad(cipher.decrypt(enc[16:]))
