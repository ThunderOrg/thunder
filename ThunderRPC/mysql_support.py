# mysql_support.py - support some basic mysql operations for ThunderRPC
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import pymysql

class mysql():
   def __init__(self, server, port):
      self.server = server
      self.port = port

   def connect(self):
      self.conn = pymysql.connect(user='thunder', passwd='thunder', db='thunder', \
                                  host=self.server, port=self.port)

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
                  "','"+profile+"') on duplicate key UPDATE ip='" + ip + "', domain='" + domain + "';")
      cur.close()

   def insertNode(self, name, address, tpe):
      cur = self.conn.cursor()
      res = cur.execute("INSERT INTO nodes VALUES ('" + name + "','" + address +         \
		  "','" + tpe + "') on duplicate key UPDATE address='" +          \
	          address + "';")
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

   def getWeights(self, id):
      cur = self.conn.cursor()
      cur.execute("SELECT * FROM weights WHERE id='"+id+"';")
      res = cur.fetchone()
      cur.close()
      return res
