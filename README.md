Preconditions:
/etc/hosts file must not contain any entries.  This is due to an issue with determining the nodes IP address in Python.  This bug should be fixed soon.

Disable firewall.  This can be done with command: sudo ufw disable if running ubuntu server.

Python3, and Python3-crypto packages must be installed.

On controller node:
Execute controller service:
python3 server.py

On each compute node:
Execute compute node service:
python3 computenode.py