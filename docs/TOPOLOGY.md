# EVPN Spine-Leaf Topology Design

## Network Topology Overview

This document describes a 2-Spine, 2-Leaf EVPN-VXLAN network topology using Cumulus Linux.

```
                    +-------------+        +-------------+
                    |   Spine-01  |        |   Spine-02  |
                    | AS 65100    |        | AS 65100    |
                    +------+------+        +------+------+
                           |                      |
                  swp1-2   |                      |   swp1-2
            +--------------+----------------------+-------------+
            |              |                      |             |
       swp51 |         swp51|                 swp52|        swp52|
            |              |                      |             |
    +-------+------+ +-----+--------+    +--------+-----+ +-----+-------+
    |   Leaf-01    | |   Leaf-02    |    |   Leaf-01    | |   Leaf-02   |
    | AS 65101     | | AS 65102     |    | AS 65101     | | AS 65102    |
    +--------------+ +--------------+    +--------------+ +--------------+
```

## IP Addressing Scheme

### Loopback Interfaces (for BGP Router-ID and VTEP)
- **Spine-01**: 10.0.0.11/32
- **Spine-02**: 10.0.0.12/32
- **Leaf-01**: 10.0.0.21/32
- **Leaf-02**: 10.0.0.22/32

### Point-to-Point Links (IPv4 Underlay)

#### Spine-01 to Leaf Switches:
- Spine-01 swp1 <-> Leaf-01 swp51: 10.1.1.0/31
  - Spine-01: 10.1.1.0/31
  - Leaf-01: 10.1.1.1/31
- Spine-01 swp2 <-> Leaf-02 swp51: 10.1.1.2/31
  - Spine-01: 10.1.1.2/31
  - Leaf-02: 10.1.1.3/31

#### Spine-02 to Leaf Switches:
- Spine-02 swp1 <-> Leaf-01 swp52: 10.1.1.4/31
  - Spine-02: 10.1.1.4/31
  - Leaf-01: 10.1.1.5/31
- Spine-02 swp2 <-> Leaf-02 swp52: 10.1.1.6/31
  - Spine-02: 10.1.1.6/31
  - Leaf-02: 10.1.1.7/31

## BGP AS Numbers

### Autonomous Systems:
- **Spine Switches (Route Reflectors)**: AS 65100
  - Spine-01: AS 65100
  - Spine-02: AS 65100
- **Leaf Switches**: Unique AS per leaf
  - Leaf-01: AS 65101
  - Leaf-02: AS 65102

## EVPN Configuration

### VNI (VXLAN Network Identifier)
- VNI 10010 - VLAN 10 (Example tenant network)
- VNI 10020 - VLAN 20 (Example tenant network)

### Route Distinguisher (RD) and Route Target (RT)
- **Leaf-01**:
  - RD: 10.0.0.21:10 (for VNI 10010)
  - RT: 65101:10
- **Leaf-02**:
  - RD: 10.0.0.22:10 (for VNI 10010)
  - RT: 65102:10

## Key Design Decisions

1. **BGP Underlay**: Uses numbered point-to-point /31 links
2. **BGP Overlay**: EVPN Address Family for MAC/IP advertisement
3. **Route Reflectors**: Both spines act as route reflectors for the EVPN overlay
4. **VXLAN**: Used as the data plane encapsulation
5. **Symmetric IRB**: For inter-VLAN routing (if required)

## Interface Naming Convention

- **swp1-48**: Regular switch ports (data plane)
- **swp49-52**: Uplink/spine ports (typically higher speed)
- **lo**: Loopback interface
- **vlan<X>**: SVI for VLANs
- **vni<X>**: VXLAN interfaces
