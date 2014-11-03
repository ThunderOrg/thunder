# Simple websocket support for ThunderRPC
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Lab
# Copyright 2014 Gabriel Jacob Loewen

from hashlib import sha1
from base64 import b64encode, b64decode
from struct import pack, unpack

def Enum(**enums):
    return type('Enum', (), enums)

# Enum of opcodes for simplicity
Opcode = Enum(
   continuation = 0x00,
   text         = 0x01,
   binary       = 0x02,
   terminate    = 0x08,
   ping         = 0x09,
   pong         = 0x10
)

# Handle websocket upgrade requests and send/receive hybi-13 websocket frames
class websocket:
   def __init__(self, request):
      self.socket = request
      self.magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

   # Test for a websocket upgrade request.  If request is valid return True.
   # Otherwise return False.
   def isHandshakePending(self, data):
      pending = False
      numKeys = 0
      dataArr = data.splitlines()
      for line in dataArr:
         lineArr = line.decode("UTF8").split(": ")
         if (lineArr[0].lower() == 'upgrade' and \
             lineArr[1].lower() == 'websocket'):
            pending = True
         elif (lineArr[0].lower() == 'sec-websocket-key'):
            numKeys+=1

      if (numKeys != 1):
         pending = False

      return pending

   # Parse the incoming request, and produce the correct handshake response.
   # Key algorithm == base64 encoded sha1 hashed incoming key prepended to
   # websocket magic value.
   def handshake(self, data):
      response = 'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket' +    \
                 '\r\nConnection: Upgrade\r\n'
      dataArr = data.splitlines()
      key = ''
      for datum in dataArr:
         if (datum.startswith('Sec-WebSocket-Key')):
            key = datum.split(': ')[1]
      if (key == ''):
         return False
      retKey = b64encode(sha1((key+self.magic).encode("UTF8")).digest())
      response += 'Sec-WebSocket-Accept: ' + retKey.decode() + '\r\n\r\n'
      return response.encode("UTF8")

   # Wrap data inside of a hybi-13 websocket frame.  Does not require masking
   # from server->client.
   def encode(self, opcode, data):
      encodedData = data.encode('UTF8')

      # Header will be 10000001
      # 1 - Finalize bit (we wont have a message that exceeds 126 characters)
      # 000 - 3 reserved bits
      # 0001 - Text opcode (UTF-8 encoded)
      # 129 in base10
      header = pack('!B', ((1 << 7) | (0 << 6) | (0 << 5) | (0 << 4) |         \
                           Opcode.text))
      payloadLen = len(encodedData)
      if (payloadLen < 126):
         header += pack('!B', payloadLen)
      elif (payloadLen < (1 << 16)):
         header += pack('>B', 126) + pack('>H', payloadLen)
      elif (payloadLen < (1 << 63)):
         header += pack('>B', 127) + pack('>Q', payloadLen)
      return bytes(header + encodedData)

   # Read a hybi-13 websocket frame and unmask the payload.
   def decode(self, data):
      payloadLen = data[1] & 127
      if (len == 126): # Two more bytes indicate length.  16-bits.
         payloadLen = unpack(">H", self.socket.recv(2))[0]
      elif (len == 127): # Eight more bytes indicate length.  Python should
                         # give us a 64-bit int.
         payloadLen = unpack(">Q", self.socket.recv(8))[0]

      # Get an array of bytes from the key
      maskingKey = self.socket.recv(4)
      mask = [byte for byte in maskingKey]

      # Get the masked data
      maskedData = self.socket.recv(payloadLen)

      # We use the masking key with mod 4 indexing to unmask the payload.
      unmasked = ''
      for byte in maskedData:
         unmasked += chr(byte ^ mask[len(unmasked) % 4])

      return unmasked
