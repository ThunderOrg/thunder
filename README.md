<h1>Thunder Vertical Cloud</h1>
<p>Thunder is primarily an Infrastructure-as-a-Service (IaaS) cloud architecture being developed for supporting virtualized guests in order to help small organizations become more cloud-aware.  The idea behind Thunder is that organizations that have limited resources and limited technical expertise may be interested in cloud computing, but do not have the experience required to deploy a sophisticated cloud architecture, such as Eucalyptus or OpenStack.  Thunder helps to alleviate these concerns by providing an automated and intuitive web-based distributed deployment system, which is built upon Cobbler.  Additionally, our intention is to provide built-in support for cost saving measures, such as power-aware load balancing, and virtual machine migration.</p>

<p>Thunder is also meant as a learning tool.  By decreasing complexity of the system architecture, cloud computing concepts can more easily be taught in the classroom.  These concepts include: hardware virtualization, scalability, elasticity, accessibility, and more.  Outlined below are a few of the concepts and a description of the approach that Thunder takes:</p>
<ul>
<li><b>Hardware virtualization</b></li>
<p> Like many open cloud architectures, Thunder uses an open virtualization API to interface with the hypervisor.  This API is called 'libvirt' (http://libvirt.org).  Libvirt gives Thunder an interface for calling low-level operations on the host, such as instantiation of virtual machine images, mounting of network storage shares (Indra nodes), networking configuration, and more.</p>
<li><b>Scalability</b></li>
<p>Scalability of an architecture is the ability for allocated resources in the cloud to scale up (increase) as the clients demands increase, and scale down (decrease) as the clients demands decrease.  For example, a client may have a large workload and wants 32gb of ram, in which case the architecture can scale up the amount of ram available to the client.  However, it could be that later on the client doesn't need as much, so the architecture can scale down to something more reasonable.  This is all possible with Thunder.</p>
<li><b>Elasticity</b></li>
<p>Elasticity of an architecture is the ability for the cloud itself to grow in a way that does not impact the running state.  For example, an elastic cloud with 4 nodes can quickly and painlessly become a 40 node cloud given the additional hardware.  Thunder supports elasticity using a number of strategies.  
<ul>
<li>Thunder nodes support ad hoc registration.  This means that by connecting a Thunder node to the network it will automagically register itself with the cloud and expose it's services to Thunder.</li>
<li>Network disruptions prompt Thunder nodes to fall back into a `searching state', in which disconnected nodes broadcast connection requests over the network.  Furthermore, Thunder also supports cooperative redundant publishers, such that if a Zeus controller goes offline a Zeus replica can take the reigns.</li>
<li>Deployment is painless using PXE booting and a web-based deployment tool based on Cobbler</li>
</ul>
<li><b>Accessibility</b></li>
<p>Traditionally, virtual machines that are instantiated in the cloud must be connected to via a separate application using either the VNC or RDP protocols.  However, this can be cumbersome because a client might just want to quickly connect and go.  Thunder allows clients to launch a virtual machine from a web browser, and then connect to it in the browser using WebSockets and HTML 5 canvas.  Of course, clients can also connect in the more traditional manner as well.</p>
</ul>

<h2>Responsibilities of Thunder services</h2>

<h3>Cloud Controller (Zeus)</h3>
<ul>
<li>ThunderRPC publisher</li>
<li>NAT Router</li>
<li>MySQL server</li>
<li>Apache2 Webserver</li>
<li>DNS server</li>
<li>VPN server</li>
</ul>

<h3>Virtualization Controller (Thor)</h3>
<ul>
<li>ThunderRPC subscriber</li>
<li>XEN / KVM host</li>
</ul>

<h3>Storage Controller (Indra)</h3>
<ul>
<li>ThunderRPC subscriber</li>
<li>NAS host (NFS and Samba)</li>
</ul>
