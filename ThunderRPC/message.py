import json

def createMessage(**kwargs):
    return json.dumps(kwargs).encode('UTF8')

def parseMessage(msg):
    if (type(msg) == type(bytes())):
       return json.loads(msg.decode('UTF8'))
    else:
       return json.loads(msg)


