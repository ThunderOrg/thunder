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
      self.magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
	  
   # Test for a websocket upgrade request.
   def isHandshakePending(self, data):
      dataArr = data.splitlines()
      for line in dataArr:
         lineArr = line.decode("UTF8").split(": ")
         if (lineArr[0].lower() == 'upgrade' and lineArr[1].lower() == 'websocket'):
            return True
      return False
	  
   # Parse the incoming request, and produce the correct handshake response.
   # Key algorithm == base64 encoded sha1 hashed incoming key prepended to websocket magic value.
   def handshake(self, data):
      response = 'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
      dataArr = data.splitlines()
      key = ''
      protocol = ''
      for i in range(0, len(dataArr), 1):
         if (dataArr[i].startswith('Sec-WebSocket-Key')):
            key = dataArr[i].split(': ')[1]
      if (key == ''):
         return False
      retKey = b64encode(sha1((key+self.magic).encode("UTF8")).digest())
      print(retKey)
      response += 'Sec-WebSocket-Accept: ' + retKey.decode() + '\r\n'
      return response.encode("UTF8")
	  
   def encode(self, opcode, data):
      # Wrap data in a hybi frame
      encodedData = data.encode('UTF8')
      # Header will be 10000001
      # 1 - Finalize bit (we wont have a message that exceeds 126 characters)
      # 000 - 3 reserved bits
      # 0001 - Text opcode (UTF-8 encoded)
      header = pack('!B', ((1 << 7) | (0 << 6) | (0 << 5) | (0 << 4) | Opcode.text))
      payloadLen = len(encodedData)
      if (payloadLen < 126):
         header += pack('!B', payloadLen)
      elif (payloadLen < (1 << 16)):
         header += pack('>B', 126) + pack('>H', payLoadLen)
      elif (payloadLen < (1 << 63)):
         header += pack('>B', 127) + pack('>Q', payloadLen)
      return bytes(header + encodedData)
	  
   def decode(self):
      header = int(self.socket.recv(2))
      fin = self.unmaskHeader(0b1000000000000000, header)
      opcode = self.unmaskHeader(0b0000111100000000, header)
      mask = self.unmaskHeader(0b0000000010000000, header)
      payloadLen = self.unmaskHeader(0b0000000001111111, header)
      print(payloadLen)
      if (opcode == Opcode.terminate or mask == 0):  # Terminate the connection
         return False
	  
      extraLen = 0
      if (len == 126): # Two more bytes indicate length.  16-bits.
         extraLen = int(self.socket.recv(2))
      elif (len == 127): # Eight more bytes indicate length.  Python should give us a 64-bit int.
         extraLen = int(self.socket.recv(8))

      payloadLen += extraLen
	   
      maskingKey = self.socket.recv(4)
      payload = self.socket.recv(payloadLen)
	   
      # We use the masking key with mod 4 indexing to unmask the payload.
      unmasked = ''
      for i in range(0, payloadLen, 1):
         unmasked += payload[i] ^ maskingKey[i % 4]

      if (opcode == Opcode.text):
         unmasked = unmasked.decode('UTF8')
	   
      return unmasked
	   
   def unmaskHeader(self, mask, data):
      unmasked = bin(x & mask).rstrip('0')[2:]
      if (unmasked == ''):
         return 0
      return int(unmasked,2)
