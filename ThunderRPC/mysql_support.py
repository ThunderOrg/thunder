# mysql_support.py - support some basic mysql operations for ThunderRPC
# Developed by Gabriel Jacob Loewen
# The University of Alabama
# Cloud and Cluster Computer Group

import mysql.connector

def getNASAddress():
   conn = mysql.connector.connect(user='root', password='thunder',             \
                                  host='localhost', db='thunder')
   cur = conn.cursor()
   cur.execute("SELECT address FROM node WHERE name='NAS';")
   res = cur.fetchone()
   cur.close()
   conn.close()
   return res[0]

def getComputeNodeAddresses():
   conn = mysql.connector.connect(user='root', password='thunder',             \
                                  host='localhost', db='thunder')
   cur = conn.cursor()
   cur.execute("SELECT address FROM node WHERE type='COMPUTE';")
   res = cur.fetchall()
   cur.close()
   conn.close()
   return res

def updateNode(name, address, tpe):
   conn = mysql.connector.connect(user='root', password='thunder',             \
                                  host='localhost', db='thunder')
   cur = conn.cursor()
   cur.execute("INSERT INTO node VALUES ('" + name + "','" + address +         \
               "','" + tpe + "') on duplicate key UPDATE address='" +          \
               address + "');")
   cur.commit()
   cur.close()
   conn.close()
