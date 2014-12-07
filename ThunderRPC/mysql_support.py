# mysql_support.py - support some basic mysql operations for ThunderRPC
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import pymysql
from time import sleep

class mysql():
   def __init__(self, server, port):
      self.server = server
      self.port = port

   def connect(self):
      while (1):
          try:
              self.conn = pymysql.connect(user='thunder', passwd='thunder', db='thunder', \
                                      host=self.server, port=self.port)
              break
          except:
              print("Couldn't connect to the database. Trying again!")
              sleep(1)
              continue

   def disconnect(self):
      self.conn.commit()
      self.conn.close()

   def getNASAddress(self, name):
      cur = self.conn.cursor()
      cur.execute("SELECT address FROM nodes WHERE type='STORAGE' AND name='"+name+"';")
      res = cur.fetchone()
      cur.close()
      return res

   def getImageData(self, name):
      cur = self.conn.cursor(pymysql.cursors.DictCursor)
      cur.execute("SELECT * FROM images WHERE name='"+name+"';")
      res = cur.fetchone()
      cur.close()
      return res

   def getProfileData(self, name):
      cur = self.conn.cursor(pymysql.cursors.DictCursor)
      cur.execute("SELECT * FROM profiles WHERE name='"+name+"';")
      res = cur.fetchone()
      cur.close()
      return res

   def getComputeNodeAddresses(self):
      cur = self.conn.cursor()
      cur.execute("SELECT address FROM node WHERE type='COMPUTE';")
      res = cur.fetchall()
      cur.close()
      return res

   def getUserInstances(self, user):
      cur = self.conn.cursor()
      cur.execute("SELECT domain, ip, node, profile FROM instances WHERE owner='"+user+"';")
      
      res = cur.fetchall()
      res = [list(row) for row in res]
      cur.close()
      return str(res)

   def deleteInstance(self, domain):
      cur = self.conn.cursor()
      cur.execute("DELETE FROM instances WHERE domain='"+domain+"';")
      cur.close()

   def insertInstance(self, domain, ip, node, owner, profile):
      cur = self.conn.cursor()
      cur.execute("INSERT INTO instances VALUES ('"+domain+"','"+ip+"','"+node+"','"+owner+ \
                  "','"+profile+"') on duplicate key UPDATE ip='" + ip + "', node='" + node + "', profile='" + profile + "';")
      cur.close()

   def updateInstanceIP(self, domain, ip):
      print("domain:",domain)
      print("ip:",ip)
      cur = self.conn.cursor()
      cur.execute("UPDATE instances SET ip='" + ip + "' WHERE domain='" + domain +"';") 
      cur.close()

   def insertNode(self, name, address, tpe):
      cur = self.conn.cursor()
      res = cur.execute("INSERT INTO nodes VALUES ('" + name + "','" + address +         \
		  "','" + tpe + "') on duplicate key UPDATE address='" +          \
	          address + "';")
      cur.close()

   def deleteNodeByName(self, name):
      cur = self.conn.cursor()
      cur.execute("DELETE FROM nodes WHERE name='"+name+"';")
      cur.close()

   def getNodeByName(self, name):
      cur = self.conn.cursor()
      cur.execute("SELECT * FROM nodes WHERE name='"+name+"';")
      res = cur.fetchone()
      cur.close()
      return res

   def deleteNodeByIP(self, ip):
      cur = self.conn.cursor()
      cur.execute("DELETE FROM nodes WHERE address='"+ip+"';")
      cur.close()

   def updateWeights(self, name, weights):
      cur = self.conn.cursor()
      ram = weights[0]
      load1 = weights[1]
      load5 = weights[2]
      load15 = weights[3]
      activevms = weights[4]
      cur.execute("UPDATE weights SET ram='" + ram + "', load1='" + load1 + \
                  "', load5='" + load5 + "', load15='" + load15 +           \
                  "', activevms='"+activevms+"' WHERE id='"+name+"';")
      cur.close()

   def getWeights(self, name):
      cur = self.conn.cursor()
      cur.execute("SELECT ram, load1, load5, load15, activevms FROM weights WHERE id='"+name+"';")
      res = cur.fetchone()
      cur.close()
      return res

   def getImages(self):
      cur = self.conn.cursor()
      cur.execute("SELECT name FROM images;")
      res = cur.fetchall()
      cur.close()
      return res

   def getProfile(self, name):
      cur = self.conn.cursor()
      cur.execute("SELECT * FROM profiles WHERE name='" + name + "';")
      res = cur.fetchone()
      cur.close()
      return res
