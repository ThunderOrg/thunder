Naming scheme and responsibility of controllers:

Cloud Controller (Zeus):
	ThunderRPC master
	NAT Router
	MySQL server
	Apache2 Webserver
	DNS server
	VPN server

Virtualization Controller (Thor):
	ThunderRPC client
	XEN / KVM host

Storage Controller (Indra):
	NAS host (NFS and Samba)
