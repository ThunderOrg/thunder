echo -e "\n\nLoading simple rc.firewall-uptables version $FWVER..\n"
DEPMOD=/sbin/depmod
MODPROBE=/sbin/modprobe

EXTIF="eth0"
INTIF="eth1"
echo "     External Interface: $EXTIF"
echo "     Internal Interface: $INTIF"

echo -en "     Loading modules: "
echo "     - Verifying that all kernel modules are ok"
$DEPMOD -a
echo "----------------------------------------------------------"

echo -en "ip_tables. "
$MODPROBE ip_tables
echo -en "nf_conntrack. "
$MODPROBE nf_conntrack
echo -en "nf_conntrack_netbios_ns. "
$MODPROBE nf_conntrack_netbios_ns
echo -en "nf_conntrack_ftp. "
$MODPROBE nf_conntrack_ftp
echo -en "nf_conntrack_tftp. "
$MODPROBE nf_conntrack_tftp
echo -en "nf_conntrack_irc. "
$MODPROBE nf_conntrack_irc
echo -en "iptable_nat. "
$MODPROBE iptable_nat
echo -en "nf_nat_ftp. "
$MODPROBE nf_nat_ftp
echo -en "nf_nat_tftp. "
$MODPROBE nf_nat_tftp

echo -e "     Done loading modules.\n"
echo "     Enabling forwarding.."
echo "1" > /proc/sys/net/ipv4/ip_forward
echo "     Enabling DynamicAddr.."
echo "1" > /proc/sys/net/ipv4/ip_dynaddr
echo "     Clearing any existing rules and setting default policy.."

iptables-restore << EOF
*nat
-A POSTROUTING -o "$EXTIF" -j MASQUERADE
COMMIT
*filter
:INPUT ACCEPT [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
-A FORWARD -i "$EXTIF" -o "$INTIF" -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
-A FORWARD -i "$INTIF" -o "$EXTIF" -j ACCEPT
-A FORWARD -j LOG
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -p udp -m state --state NEW -m udp --dport 69 -j ACCEPT
COMMIT
EOF
/etc/init.d/networking restart
echo -e "\nrc.firewall-iptables v$FWVER done.\n"
