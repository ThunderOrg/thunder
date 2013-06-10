import base64
from Crypto import Random
from Crypto.Random import random
from Crypto.Cipher import AES

k = b'YM{<GC\xdaQ\x80\xe8\xd8\xcf\xf1\xf7\xdaM'

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(chr(s[-1]))]

def generateNonce():
   return str(random.getrandbits(32))

def encrypt( raw ):
   raw = pad(raw)
   iv = Random.new().read( AES.block_size )
   cipher = AES.new( k, AES.MODE_CBC, iv )
   return base64.b64encode( iv + cipher.encrypt( raw ) ) 

def decrypt( enc ):
   enc = base64.b64decode(enc)
   iv = enc[:16]
   cipher = AES.new( k, AES.MODE_CBC, iv )
   return unpad( cipher.decrypt( enc[16:] ))
