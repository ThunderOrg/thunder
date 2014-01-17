from hashlib import sha1
from base64 import b64encode, b64decode
from struct import pack, unpack
from enum import Enum

Opcode = Enum(
   continuation = 0x00,
   text         = 0x01,
   binary       = 0x02,
   terminate    = 0x08,
   ping         = 0x09,
   pong         = 0x10
)

class websocket:
   def __init__(self, request):
      self.socket = request
      self.magic = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
	  
   # Test for a websocket upgrade request.
   def isHandshakePending(self, data):
      dataArr = data.splitlines()
      for line in dataArr:
         lineArr = line.split(b': ')
         if (lineArr[0].lower() == b'upgrade' and lineArr[1].lower() == b'websocket'):
            return True
      return False
	  
   # Parse the incoming request, and produce the correct handshake response.
   # Key algorithm == base64 encoded sha1 hashed incoming key prepended to websocket magic value.
   def handshake(self, data):
      response = b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
      dataArr = data.splitlines()
      key = b''
      protocol = b''
      for i in range(0, len(dataArr), 1):
         if (dataArr[i].startswith(b'Sec-WebSocket-Key')):
            key = dataArr[i].split(b': ')[1]
         elif (dataArr[i].startswith(b'Sec-WebSocket-Protocol')):
            protocol = dataArr[i].split(b': ')[1]
      if (key == b''):
         return False
      retKey = b64encode(sha1(key+self.magic).digest())
      response += b'Sec-WebSocket-Accept: ' + retKey + b'\r\n'
     
      return response
	  
   def encode(self, opcode, data):
      # Wrap data in a websocket frame
      encodedData = data.encode('UTF-8')
      buffer = b''
      b1 = 0x80 | opcode # FIN + opcode
      b2 = 0
      payloadLen = len(encodedData)
      print(payloadLen)
      if (payloadLen <= 125):
         # Format of bytes == big-endian (>) 2 unsigned chars (BB)
         b2 |= payloadLen
         buffer += pack(">BB", b1, b2)
      elif (payloadLen >= 126 and payloadLen <= 65535):
         # Format of bytes == big-endian (>) 2 unsigned chars (BB) and one unsigned short (H)
         b2 |= 126
         buffer += pack(">BBH", b1, b2, payloadLen)
      elif (payloadLen == 127):
         # Format of bytes == big-endian (>) 2 unsigned chars (BB) and one unsigned long long (Q)
         b2 |= 127
         buffer += pack(">BBQ", b1, b2, payloadLen)
  
      # Something bad happened if this is true...
      if buffer == None:
         return None
  
      print(buffer+encodedData)

      return buffer+encodedData

   def decode(self):
      header = int(self.socket.recv(4))
      fin = self.unmaskHeader(0b1000000000000000, header)
      opcode = self.unmaskHeader(0b0000111100000000, header)
      mask = self.unmaskHeader(0b0000000010000000, header)
      payloadLen = self.unmaskHeader(0b0000000001111111, header)

      if (opcode == Opcode.terminate or mask == 0):  # Terminate the connection
         return False

      extraLen = 0
      if (len == 126): # Two more bytes indicate length
         extraLen = int(self.socket.recv(2))
      elif (len == 127): # Eight more bytes indicate length
         extraLen = int(self.socket.recv(8))

      payloadLen += extraLen

      maskingKey = self.socket.recv(4)
      payload = self.socket.recv(payloadLen)

      # We use the masking key with mod 4 indexing to unmask the payload.
      unmasked = ''
      for i in range(0, len(payload), 1):
         unmasked += payload[i] ^ maskingKey[i % 4]
         if (opcode == Opcode.text):
            unmasked = unmasked.decode('UTF-8')

      return unmasked
	   
   def unmaskHeader(self, mask, data):
      unmasked = bin(x & mask).rstrip('0')[2:]
      if (unmasked == ''):
         return 0
      return int(unmasked,2)
