# EVPN Configuration Reference

Quick reference guide for the EVPN Spine-Leaf topology configuration.

## Network Diagram

```
                    10.0.0.11/32            10.0.0.12/32
                    +-----------+           +-----------+
                    | Spine-01  |           | Spine-02  |
                    | AS 65100  |           | AS 65100  |
                    | (RR)      |           | (RR)      |
                    +-----+-----+           +-----+-----+
                          |                       |
                    swp1  |  swp2           swp1  |  swp2
               10.1.1.0/31|  10.1.1.2/31    10.1.1.4/31|  10.1.1.6/31
                          |                       |
             +------------+----------+------------+------------+
             |            |          |            |            |
       swp51 |      swp51 |    swp52 |      swp52 |            |
    10.1.1.1 |   10.1.1.3 |  10.1.1.5|   10.1.1.7 |            |
             |            |          |            |            |
        +----+----+  +----+----+     +----+----+  +----+----+
        | Leaf-01 |  | Leaf-02 |     | Leaf-01 |  | Leaf-02 |
        | AS      |  | AS      |     | AS      |  | AS      |
        | 65101   |  | 65102   |     | 65101   |  | 65102   |
        +---------+  +---------+     +---------+  +---------+
        10.0.0.21/32 10.0.0.22/32    (VTEP IPs)
```

## Quick Reference Tables

### Switch Loopback Addresses

| Switch   | Loopback IP  | Purpose                    |
|----------|--------------|----------------------------|
| Spine-01 | 10.0.0.11/32 | BGP Router-ID              |
| Spine-02 | 10.0.0.12/32 | BGP Router-ID              |
| Leaf-01  | 10.0.0.21/32 | BGP Router-ID & VTEP       |
| Leaf-02  | 10.0.0.22/32 | BGP Router-ID & VTEP       |

### Point-to-Point Links

| Connection            | Spine Port | Spine IP    | Leaf Port | Leaf IP     |
|-----------------------|------------|-------------|-----------|-------------|
| Spine-01 ↔ Leaf-01   | swp1       | 10.1.1.0/31 | swp51     | 10.1.1.1/31 |
| Spine-01 ↔ Leaf-02   | swp2       | 10.1.1.2/31 | swp51     | 10.1.1.3/31 |
| Spine-02 ↔ Leaf-01   | swp1       | 10.1.1.4/31 | swp52     | 10.1.1.5/31 |
| Spine-02 ↔ Leaf-02   | swp2       | 10.1.1.6/31 | swp52     | 10.1.1.7/31 |

### BGP Autonomous Systems

| Switch   | AS Number | Role                    |
|----------|-----------|-------------------------|
| Spine-01 | 65100     | Route Reflector         |
| Spine-02 | 65100     | Route Reflector         |
| Leaf-01  | 65101     | EVPN PE (Provider Edge) |
| Leaf-02  | 65102     | EVPN PE (Provider Edge) |

### VLAN and VNI Mapping

| VLAN | VNI   | Purpose        | Leaf-01 SVI      | Leaf-02 SVI      |
|------|-------|----------------|------------------|------------------|
| 10   | 10010 | Tenant Network | 192.168.10.1/24  | 192.168.10.2/24  |
| 20   | 10020 | Tenant Network | 192.168.20.1/24  | 192.168.20.2/24  |

## Configuration File Locations

### On Cumulus Linux Switches

```
/etc/hostname              # Switch hostname
/etc/network/interfaces    # Network interface configuration
/etc/frr/frr.conf         # FRR routing configuration
/etc/frr/daemons          # FRR daemon enable/disable
```

### In This Repository

```
configs/spine/spine-01.conf    # Spine-01 configuration
configs/spine/spine-02.conf    # Spine-02 configuration
configs/leaf/leaf-01.conf      # Leaf-01 configuration
configs/leaf/leaf-02.conf      # Leaf-02 configuration
```

## Key BGP Configuration

### Spine Switches (Route Reflector)

```
router bgp 65100
 bgp router-id 10.0.0.11
 neighbor LEAF peer-group
 neighbor LEAF remote-as external
 neighbor swp1 interface peer-group LEAF
 neighbor swp2 interface peer-group LEAF
 !
 address-family l2vpn evpn
  neighbor LEAF activate
  neighbor LEAF route-reflector-client
 exit-address-family
```

### Leaf Switches (PE)

```
router bgp 65101
 bgp router-id 10.0.0.21
 neighbor SPINE peer-group
 neighbor SPINE remote-as external
 neighbor swp51 interface peer-group SPINE
 neighbor swp52 interface peer-group SPINE
 !
 address-family l2vpn evpn
  neighbor SPINE activate
  advertise-all-vni
 exit-address-family
```

## VXLAN Configuration (Leaf Switches)

### Bridge Configuration

```
auto bridge
iface bridge
    bridge-ports vni10 vni20
    bridge-vlan-aware yes
    bridge-vids 10 20
    bridge-pvid 1
```

### VNI Configuration

```
auto vni10
iface vni10
    vxlan-id 10010
    vxlan-local-tunnelip 10.0.0.21
    bridge-access 10
    bridge-learning off
    bridge-arp-nd-suppress on
```

## Common Commands

### Show Commands

```bash
# BGP Status
sudo vtysh -c 'show bgp summary'
sudo vtysh -c 'show bgp l2vpn evpn summary'

# BGP Routes
sudo vtysh -c 'show ip bgp'
sudo vtysh -c 'show bgp l2vpn evpn route'

# Interface Status
sudo net show interface
ip link show
ip addr show

# VXLAN Status
ip -d link show type vxlan
sudo bridge fdb show | grep dst

# Bridge Status
sudo bridge vlan show
sudo brctl show
```

### Configuration Commands

```bash
# Reload Network Configuration
sudo ifreload -a

# Restart FRR
sudo systemctl restart frr

# Check FRR Status
sudo systemctl status frr

# Access FRR CLI
sudo vtysh
```

### Troubleshooting Commands

```bash
# Check Logs
sudo tail -f /var/log/syslog
sudo tail -f /var/log/frr/frr.log

# Check BGP Neighbors
sudo vtysh -c 'show bgp neighbor'

# Check Routes Advertised
sudo vtysh -c 'show bgp neighbor <neighbor-ip> advertised-routes'

# Check Routes Received
sudo vtysh -c 'show bgp neighbor <neighbor-ip> routes'

# Ping Test
ping 10.0.0.21  # Test loopback connectivity
```

## File Structure Reference

```
NVIDIA-VXLAN/
├── README.md                       # Main documentation
├── configs/                        # Configuration templates
│   ├── spine/
│   │   ├── spine-01.conf          # Spine-01 config
│   │   └── spine-02.conf          # Spine-02 config
│   └── leaf/
│       ├── leaf-01.conf           # Leaf-01 config
│       └── leaf-02.conf           # Leaf-02 config
├── scripts/                        # Automation scripts
│   ├── deploy_evpn.py             # Main deployment script
│   ├── inventory.yaml             # Switch inventory
│   └── requirements.txt           # Python dependencies
└── docs/                          # Documentation
    ├── TOPOLOGY.md                # Topology design
    ├── AUTOMATION.md              # Automation guide
    ├── QUICKSTART.md              # Quick start guide
    └── REFERENCE.md               # This file
```

## Protocol Stack

```
┌─────────────────────────────────────┐
│     Application (VMs, Containers)   │
├─────────────────────────────────────┤
│     VLAN (Layer 2 Network)          │
├─────────────────────────────────────┤
│     VXLAN (Encapsulation)           │
├─────────────────────────────────────┤
│     EVPN (Control Plane)            │
├─────────────────────────────────────┤
│     BGP (Routing Protocol)          │
├─────────────────────────────────────┤
│     IP (Underlay Network)           │
├─────────────────────────────────────┤
│     Physical Layer (Ethernet)       │
└─────────────────────────────────────┘
```

## Address Space Allocation

### Underlay (Physical Network)
- **Loopbacks**: 10.0.0.0/24
  - Spines: 10.0.0.11-12
  - Leafs: 10.0.0.21-22
- **P2P Links**: 10.1.1.0/24
  - Allocated as /31 subnets

### Overlay (Tenant Networks)
- **VLAN 10**: 192.168.10.0/24
- **VLAN 20**: 192.168.20.0/24

### Management Network
- Defined in inventory.yaml (typically 192.168.1.0/24 or similar)

## Route Types in EVPN

| Type | Description                  | Purpose                          |
|------|------------------------------|----------------------------------|
| 2    | MAC/IP Advertisement Route   | Advertise host MAC and IP        |
| 3    | Inclusive Multicast Route    | BUM traffic handling (IMET)      |
| 5    | IP Prefix Route              | IP routing between VRFs          |

## Deployment Order

1. **Spine-01** (Route Reflector)
2. **Spine-02** (Route Reflector)
3. Wait 2-3 minutes for BGP convergence
4. **Leaf-01** (PE)
5. **Leaf-02** (PE)

## Expected BGP States

### Normal Operation

```
Neighbor        V    AS   MsgRcvd   MsgSent   Up/Down  State/PfxRcd
swp1            4 65101      100       100   01:30:00        5
swp2            4 65102       98        99   01:28:00        5
```

State should be showing prefix count (5 in this example).

### Problem States

- **Idle**: BGP not configured or interface down
- **Connect**: TCP connection issue
- **Active**: Interface up but BGP session not establishing
- **OpenSent/OpenConfirm**: BGP negotiation in progress

## Scale Considerations

### Current Design
- 2 Spine switches
- 2 Leaf switches
- 2 VLANs/VNIs
- Supports ~100 hosts per leaf

### Expansion Capacity
- Can scale to 4-8 spine switches
- Can scale to 64+ leaf switches
- Can support 4000+ VNIs
- Limited by hardware capabilities

## Security Considerations

1. **BGP Authentication**: Not configured (add MD5 auth in production)
2. **Management Access**: Secure with SSH keys
3. **Console Access**: Physical security required
4. **Route Filtering**: Consider adding route-maps
5. **BFD**: Consider enabling for faster failure detection

## Performance Tuning

### BGP Timers (Default)
- Keepalive: 3 seconds
- Hold time: 9 seconds

### To modify timers:
```
router bgp 65100
 neighbor LEAF timers 3 9
```

### BFD (Optional for faster convergence)
```
router bgp 65100
 neighbor LEAF bfd
```

## Monitoring Recommendations

1. **BGP Session State**: Should always be "Established"
2. **Interface Status**: All configured interfaces should be "UP"
3. **VXLAN Tunnel Count**: Should match number of remote VTEPs
4. **Route Count**: Stable route count indicates healthy network
5. **Packet Loss**: Monitor with ping/iperf tests

## Backup and Recovery

### Automatic Backups
The deployment script automatically creates backups:
```
/etc/network/interfaces.backup.YYYYMMDD-HHMMSS
/etc/frr/frr.conf.backup.YYYYMMDD-HHMMSS
```

### Manual Backup
```bash
sudo cp /etc/network/interfaces /etc/network/interfaces.backup
sudo cp /etc/frr/frr.conf /etc/frr/frr.conf.backup
```

### Restore
```bash
sudo cp /etc/network/interfaces.backup /etc/network/interfaces
sudo cp /etc/frr/frr.conf.backup /etc/frr/frr.conf
sudo ifreload -a
sudo systemctl restart frr
```

## Additional Resources

- [NVIDIA Cumulus Linux Docs](https://docs.nvidia.com/networking-ethernet-software/cumulus-linux/)
- [EVPN RFC 7432](https://tools.ietf.org/html/rfc7432)
- [VXLAN RFC 7348](https://tools.ietf.org/html/rfc7348)
- [FRR Documentation](https://docs.frrouting.org/)

---

This reference guide is part of the NVIDIA-VXLAN repository.
For detailed guides, see:
- [QUICKSTART.md](QUICKSTART.md) - Quick deployment guide
- [AUTOMATION.md](AUTOMATION.md) - Detailed automation documentation
- [TOPOLOGY.md](TOPOLOGY.md) - Network design details
