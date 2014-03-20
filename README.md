<h2>Thunder Vertical Cloud</h2>
<p>Thunder is primarily an Infrastructure-as-a-Service (IaaS) cloud architecture being developed as an infrstructure for supporting virtualized guests using an intuitive web-based graphical interface.  The idea behind Thunder is that organizations that have limited resources and technical expertise may be interested in cloud computing, but do not have the experience required to deploy a more sophisticated cloud architecture, such as Eucalyptus or OpenStack.  Thunder helps to alleviate these concerns by providing an automated and intuitive web-based distributed deployment system, which is built upon Cobbler.  Additionally, our intention is to provide built-in support for cost saving measures, such as power-aware load balancing, and virtual machine migration.</p>

<h2>Naming scheme and responsibility of Thunder services</h2>

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
<li>NAS host (NFS and Samba)</li>
</ul>
