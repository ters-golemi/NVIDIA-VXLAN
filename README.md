# NVIDIA-VXLAN
Ethernet VPN (EVPN) Spine-Leaf Topology Configuration and Automation

## Overview

This repository provides configuration templates and automation tools for deploying an EVPN (Ethernet VPN) based Spine-Leaf topology using Cumulus Linux switches. It includes configurations for a 2-Spine, 2-Leaf architecture with VXLAN overlay network.

## Features

- ✅ Pre-configured templates for Spine and Leaf switches
- ✅ Complete IP addressing scheme and BGP AS design
- ✅ EVPN-VXLAN overlay network configuration
- ✅ Python automation script for deployment
- ✅ Comprehensive documentation
- ✅ Easy to customize and extend

## Repository Structure

```
NVIDIA-VXLAN/
├── configs/                  # Switch configuration files
│   ├── spine/               # Spine switch configurations
│   │   ├── spine-01.conf
│   │   └── spine-02.conf
│   └── leaf/                # Leaf switch configurations
│       ├── leaf-01.conf
│       └── leaf-02.conf
├── scripts/                 # Automation scripts
│   ├── deploy_evpn.py      # Main deployment script
│   ├── inventory.yaml      # Switch inventory file
│   └── requirements.txt    # Python dependencies
├── docs/                    # Documentation
│   ├── TOPOLOGY.md         # Topology design and IP scheme
│   └── AUTOMATION.md       # Automation guide
└── README.md               # This file
```

## Network Topology

```
            +-------------+        +-------------+
            |  Spine-01   |        |  Spine-02   |
            | AS 65100    |        | AS 65100    |
            +------+------+        +------+------+
                   |                      |
        swp1-2     |                      |   swp1-2
    +--------------+----------------------+-------------+
    |              |                      |             |
swp51|         swp51|                 swp52|        swp52|
    |              |                      |             |
+---+------+ +-----+--------+    +--------+-----+ +-----+-------+
| Leaf-01  | |   Leaf-02    |    |   Leaf-01    | |   Leaf-02   |
| AS 65101 | | AS 65102     |    | AS 65101     | | AS 65102    |
+----------+ +--------------+    +--------------+ +--------------+
```

### Key Design Elements

- **Underlay**: BGP with numbered point-to-point links (/31 subnets)
- **Overlay**: EVPN Address Family for MAC/IP advertisement
- **Encapsulation**: VXLAN for data plane
- **Route Reflectors**: Both spine switches act as BGP route reflectors
- **VNI**: Support for multiple tenant networks (VNI 10010, 10020)

## Quick Start

### Prerequisites

- Python 3.6 or higher
- SSH access to Cumulus Linux switches
- Management network connectivity

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ters-golemi/NVIDIA-VXLAN.git
   cd NVIDIA-VXLAN
   ```

2. Install Python dependencies:
   ```bash
   pip install -r scripts/requirements.txt
   ```

3. Update the inventory file with your switch details:
   ```bash
   vi scripts/inventory.yaml
   ```

4. Deploy the configuration:
   ```bash
   cd scripts
   python3 deploy_evpn.py --inventory inventory.yaml
   ```

## Configuration Details

### IP Addressing Scheme

**Loopback Interfaces:**
- Spine-01: 10.0.0.11/32
- Spine-02: 10.0.0.12/32
- Leaf-01: 10.0.0.21/32
- Leaf-02: 10.0.0.22/32

**Point-to-Point Links:**
- Uses /31 subnets from 10.1.1.0/24 range
- See [TOPOLOGY.md](docs/TOPOLOGY.md) for complete details

### BGP Configuration

- **Spine AS**: 65100 (shared by both spines)
- **Leaf AS**: 65101 (Leaf-01), 65102 (Leaf-02)
- **Route Reflector**: Spines act as RR for EVPN
- **Address Families**: IPv4 Unicast and L2VPN EVPN

## Usage

### Dry-Run Mode

Test the deployment without making changes:
```bash
python3 deploy_evpn.py --inventory inventory.yaml --dry-run
```

### Deploy to Specific Switches

Deploy only to spine or leaf switches:
```bash
# Spines only
python3 deploy_evpn.py --inventory inventory.yaml --switches spine-01 spine-02

# Leafs only
python3 deploy_evpn.py --inventory inventory.yaml --switches leaf-01 leaf-02
```

### Verification

After deployment, verify the configuration:

```bash
# Check BGP status
sudo vtysh -c 'show bgp summary'

# Check EVPN status
sudo vtysh -c 'show bgp l2vpn evpn summary'

# Check VXLAN tunnels
sudo bridge fdb show | grep vni
```

## Documentation

- **[TOPOLOGY.md](docs/TOPOLOGY.md)**: Detailed network topology, IP scheme, and design decisions
- **[AUTOMATION.md](docs/AUTOMATION.md)**: Complete automation guide with troubleshooting

## Customization

### Adding More Switches

1. Create new configuration files in `configs/spine/` or `configs/leaf/`
2. Add entries to `scripts/inventory.yaml`
3. Update IP addresses and AS numbers according to your design

### Modifying VLANs/VNIs

Edit the leaf configuration files to add or modify:
- VLAN definitions
- VNI mappings
- SVI (Switched Virtual Interface) configuration

### Changing IP Scheme

Update the following in configuration files:
- Loopback addresses
- Point-to-point link addresses
- BGP router IDs

## Troubleshooting

Common issues and solutions:

1. **Connection failures**: Verify management IP and SSH access
2. **BGP not establishing**: Check interface status and IP connectivity
3. **EVPN routes missing**: Verify VXLAN interfaces and bridge configuration

See [AUTOMATION.md](docs/AUTOMATION.md) for detailed troubleshooting steps.

## Requirements

### Hardware
- Cumulus Linux switches (4.x or 5.x)
- Properly cabled physical topology

### Software
- Python 3.6+
- paramiko (SSH library)
- PyYAML (YAML parser)

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Bug fixes
- Feature enhancements
- Documentation improvements
- Additional templates

## License

This project is provided as-is for educational and operational purposes.

## Support

For issues and questions:
- Review the documentation in the `docs/` directory
- Check the troubleshooting guide in [AUTOMATION.md](docs/AUTOMATION.md)
- Open a GitHub issue with detailed information

## References

- [NVIDIA Cumulus Linux Documentation](https://docs.nvidia.com/networking-ethernet-software/cumulus-linux/)
- [EVPN Technical Overview](https://docs.nvidia.com/networking-ethernet-software/cumulus-linux/Layer-3/EVPN/)
- [VXLAN Configuration Guide](https://docs.nvidia.com/networking-ethernet-software/cumulus-linux/Network-Virtualization/)
- [FRR Documentation](https://docs.frrouting.org/)

## Authors

This configuration and automation framework is designed for NVIDIA/Cumulus Linux environments implementing EVPN-VXLAN overlay networks.

---

**Note**: Always test configurations in a lab environment before deploying to production networks.
