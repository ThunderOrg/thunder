# mysql_support.py - support some basic mysql operations for ThunderRPC
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import pymysql

def connect():
   conn = pymysql.connect(unix_socket='/var/run/mysqld/mysqld.sock', user='root', passwd='thunder',             \
                                  host='127.0.0.1', db='thunder')
   return conn

def getNASAddress(name):
   conn = connect()
   cur = conn.cursor()
   cur.execute("SELECT address FROM nodes WHERE type='STORAGE' AND name='"+name+"';")
   res = cur.fetchall()
   cur.close()
   conn.close()
   return res[0]

def getImageData(name):
   conn = connect()
   cur = conn.cursor(pymysql.cursors.DictCursor)
   cur.execute("SELECT * FROM images WHERE distro='"+name+"';")
   res = cur.fetchone()
   cur.close()
   conn.close()
   return res

def getComputeNodeAddresses():
   conn = connect()
   cur = conn.cursor()
   cur.execute("SELECT address FROM node WHERE type='COMPUTE';")
   res = cur.fetchall()
   cur.close()
   conn.close()
   return res

def deleteInstance(domain):
   conn = connect()
   cur = conn.cursor()
   cur.execute("DELETE FROM instances WHERE domain='"+domain+"';")
   cur.close()
   conn.close()

def insertInstance(domain, ip):
   conn = connect()
   cur = conn.cursor()
   cur.execute("INSERT INTO instances VALUES ("+domain+","+ip+");")
   cur.close()
   conn.close()

def updateNode(name, address, tpe):
   conn = connect()
   cur = conn.cursor()
   cur.execute("INSERT INTO node VALUES ('" + name + "','" + address +         \
               "','" + tpe + "') on duplicate key UPDATE address='" +          \
               address + "');")
   cur.commit()
   cur.close()
   conn.close()
