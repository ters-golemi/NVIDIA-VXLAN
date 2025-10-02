# EVPN Automation Guide

This guide explains how to use the Python automation script to deploy EVPN configuration to Cumulus Linux switches.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Script Overview](#script-overview)
3. [Setup and Installation](#setup-and-installation)
4. [Configuration Files](#configuration-files)
5. [Deployment Process](#deployment-process)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Software Requirements
- Python 3.6 or higher
- Required Python packages:
  - `paramiko` - For SSH connections
  - `pyyaml` - For YAML parsing

### Network Requirements
- Management network connectivity to all switches
- SSH access enabled on all switches
- Management IP addresses configured on switches
- Valid credentials (username/password)

### Switch Requirements
- Cumulus Linux 4.x or 5.x
- FRR (Free Range Routing) installed
- Sufficient privileges to modify system configuration

## Script Overview

The `deploy_evpn.py` script automates the following tasks:

1. **Connection Management**: Establishes SSH connections to switches
2. **Configuration Backup**: Creates timestamped backups of existing configurations
3. **Configuration Deployment**: Deploys network interfaces and FRR configurations
4. **Service Management**: Reloads networking and restarts FRR services
5. **Verification**: Checks BGP and EVPN status after deployment

### Script Features
- ✅ Automated deployment to multiple switches
- ✅ Configuration backup before changes
- ✅ Dry-run mode for testing
- ✅ Selective switch deployment
- ✅ Status verification
- ✅ Detailed logging and error reporting

## Setup and Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/ters-golemi/NVIDIA-VXLAN.git
cd NVIDIA-VXLAN
```

### Step 2: Install Python Dependencies

```bash
pip install paramiko pyyaml
```

Or use a requirements file:

```bash
# Create requirements.txt
cat > scripts/requirements.txt << EOF
paramiko>=2.7.0
pyyaml>=5.3.0
EOF

# Install dependencies
pip install -r scripts/requirements.txt
```

### Step 3: Configure Management Access

Ensure you have management network access to all switches. The switches should have:
- Management IP addresses configured
- SSH server running
- Valid user credentials

Example Cumulus Linux management configuration:
```bash
# On each switch, configure management interface
sudo vi /etc/network/interfaces

# Add management interface
auto eth0
iface eth0 inet static
    address 192.168.1.11/24  # Unique per switch
    gateway 192.168.1.1
```

## Configuration Files

### Directory Structure

```
NVIDIA-VXLAN/
├── configs/
│   ├── spine/
│   │   ├── spine-01.conf
│   │   └── spine-02.conf
│   └── leaf/
│       ├── leaf-01.conf
│       └── leaf-02.conf
├── scripts/
│   ├── deploy_evpn.py
│   └── inventory.yaml
└── docs/
    ├── TOPOLOGY.md
    └── AUTOMATION.md
```

### Inventory File (inventory.yaml)

The inventory file contains connection details for all switches:

```yaml
switches:
  spine-01:
    hostname: 192.168.1.11      # Management IP
    username: cumulus            # SSH username
    password: CumulusLinux!      # SSH password
    port: 22                     # SSH port
    role: spine
    config_file: spine/spine-01.conf
  
  # ... additional switches
```

**Important**: Update the inventory file with your actual:
- Management IP addresses
- Credentials (username/password)
- Configuration file paths

### Configuration Files Format

Each switch configuration file contains three sections:

1. **Hostname Configuration**: Sets the switch hostname
2. **Network Interfaces**: Configures loopback and physical interfaces
3. **FRR Configuration**: BGP and EVPN settings

Example structure:
```
# /etc/hostname
# spine-01

# /etc/network/interfaces
auto lo
iface lo inet loopback
    address 10.0.0.11/32
...

# /etc/frr/frr.conf
router bgp 65100
...
```

## Deployment Process

### Method 1: Deploy to All Switches

```bash
cd scripts
python3 deploy_evpn.py --inventory inventory.yaml
```

### Method 2: Dry-Run (Test Without Changes)

```bash
python3 deploy_evpn.py --inventory inventory.yaml --dry-run
```

### Method 3: Deploy to Specific Switches

```bash
# Deploy only to spine switches
python3 deploy_evpn.py --inventory inventory.yaml --switches spine-01 spine-02

# Deploy only to leaf switches
python3 deploy_evpn.py --inventory inventory.yaml --switches leaf-01 leaf-02

# Deploy to a single switch
python3 deploy_evpn.py --inventory inventory.yaml --switches spine-01
```

### Method 4: Custom Configuration Directory

```bash
python3 deploy_evpn.py --inventory inventory.yaml --config-dir /path/to/configs
```

## Deployment Workflow

The script performs the following steps for each switch:

1. **Connect**: Establish SSH connection
   ```
   ✓ Connected to 192.168.1.11
   ```

2. **Backup**: Create configuration backups
   ```
   ✓ Configuration backed up on 192.168.1.11
   ```

3. **Set Hostname**: Configure the switch hostname
   ```
   ✓ Set hostname to spine-01
   ```

4. **Deploy Interfaces**: Apply network interface configuration
   ```
   ✓ Deployed interfaces configuration to 192.168.1.11
   ```

5. **Deploy FRR**: Apply BGP/EVPN configuration
   ```
   ✓ Deployed FRR configuration to 192.168.1.11
   ```

6. **Reload Networking**: Apply network changes
   ```
   ✓ Reloaded networking on 192.168.1.11
   ```

7. **Restart FRR**: Restart routing daemon
   ```
   ✓ Restarted FRR on 192.168.1.11
   ```

8. **Verify**: Check BGP and EVPN status
   ```
   --- BGP Summary on 192.168.1.11 ---
   --- EVPN Summary on 192.168.1.11 ---
   ```

## Verification

### Automated Verification

The script automatically verifies:
- BGP neighbor status
- EVPN status

### Manual Verification

After deployment, you can manually verify the configuration:

#### 1. Check BGP Status

```bash
# On any switch
sudo vtysh -c 'show bgp summary'
```

Expected output: BGP neighbors should be in "Established" state.

#### 2. Check EVPN Status

```bash
sudo vtysh -c 'show bgp l2vpn evpn summary'
```

Expected output: EVPN neighbors should be active.

#### 3. Check VXLAN Status (Leaf Switches)

```bash
sudo bridge fdb show | grep vni
```

Expected output: VXLAN tunnel endpoints should be listed.

#### 4. Check Interface Status

```bash
sudo net show interface
```

Expected output: All configured interfaces should be "UP".

#### 5. Check Route Advertisements

```bash
# On leaf switches
sudo vtysh -c 'show bgp l2vpn evpn route'
```

Expected output: Type-2 (MAC/IP) and Type-3 (IMET) routes.

## Alternative Deployment Methods

### Method 1: Using Ansible

For larger deployments, consider using Ansible:

```yaml
# playbook.yml
- hosts: switches
  tasks:
    - name: Deploy interfaces configuration
      copy:
        src: "configs/{{ inventory_hostname }}.conf"
        dest: /etc/network/interfaces
    
    - name: Reload networking
      command: ifreload -a
```

### Method 2: Manual Deployment via SCP

```bash
# Copy configuration to switch
scp configs/spine/spine-01.conf cumulus@192.168.1.11:/tmp/

# SSH to switch and apply
ssh cumulus@192.168.1.11
sudo cp /tmp/spine-01.conf /etc/network/interfaces
sudo ifreload -a
```

### Method 3: Using NCLU (Network Command Line Utility)

Cumulus Linux supports NCLU for configuration:

```bash
# Example for configuring BGP
net add bgp autonomous-system 65100
net add bgp router-id 10.0.0.11
net commit
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to switch
```
✗ Failed to connect to 192.168.1.11: [Errno 111] Connection refused
```

**Solutions**:
1. Verify management IP address is correct
2. Check SSH service is running: `sudo systemctl status ssh`
3. Verify firewall rules allow SSH
4. Test connectivity: `ping 192.168.1.11`

### Authentication Failures

**Problem**: Authentication failed
```
✗ Failed to connect to 192.168.1.11: Authentication failed
```

**Solutions**:
1. Verify username and password in inventory.yaml
2. Check account is not locked: `sudo passwd -S cumulus`
3. Ensure SSH key-based auth is not required

### Configuration Deployment Failures

**Problem**: Failed to deploy configuration
```
✗ Failed to deploy interfaces config: Permission denied
```

**Solutions**:
1. Verify user has sudo privileges
2. Check file permissions on configuration files
3. Ensure sufficient disk space: `df -h`

### BGP Not Establishing

**Problem**: BGP neighbors not coming up

**Solutions**:
1. Check interface status: `sudo net show interface`
2. Verify IP connectivity: `ping <neighbor-ip>`
3. Check BGP configuration: `sudo vtysh -c 'show run bgp'`
4. Review logs: `sudo tail -f /var/log/frr/frr.log`

### EVPN Issues

**Problem**: EVPN routes not being advertised

**Solutions**:
1. Verify VXLAN interfaces are up: `ip -d link show type vxlan`
2. Check bridge configuration: `sudo brctl show`
3. Verify advertise-all-vni is configured: `sudo vtysh -c 'show run bgp'`

## Best Practices

1. **Always test in dry-run mode first**
   ```bash
   python3 deploy_evpn.py --inventory inventory.yaml --dry-run
   ```

2. **Deploy spines before leafs**
   ```bash
   python3 deploy_evpn.py --inventory inventory.yaml --switches spine-01 spine-02
   # Wait for stability
   python3 deploy_evpn.py --inventory inventory.yaml --switches leaf-01 leaf-02
   ```

3. **Keep configuration backups**
   - The script automatically creates backups
   - Backups are stored with timestamps: `/etc/network/interfaces.backup.YYYYMMDD-HHMMSS`

4. **Use version control for configurations**
   - Store all configuration files in git
   - Track changes and review before deployment

5. **Test on a single switch first**
   ```bash
   python3 deploy_evpn.py --inventory inventory.yaml --switches spine-01
   ```

6. **Monitor during deployment**
   - Watch for error messages
   - Verify each switch before moving to the next

7. **Document your environment**
   - Update inventory.yaml with accurate information
   - Document any customizations in comments

## Security Considerations

1. **Credential Management**
   - Don't commit passwords to git
   - Use environment variables or secret management tools
   - Consider SSH key-based authentication

2. **Network Isolation**
   - Use a dedicated management network
   - Restrict SSH access with firewall rules
   - Use VPN for remote access

3. **Change Management**
   - Test in a lab environment first
   - Schedule maintenance windows
   - Have rollback procedures ready

## Advanced Usage

### Using Environment Variables for Credentials

```bash
export SWITCH_USERNAME="cumulus"
export SWITCH_PASSWORD="SecurePassword"

# Modify script to read from environment
```

### Parallel Deployment

```bash
# Deploy spines in parallel
python3 deploy_evpn.py --switches spine-01 &
python3 deploy_evpn.py --switches spine-02 &
wait
```

### Integration with CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy EVPN Configuration

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r scripts/requirements.txt
      - name: Deploy configuration
        run: |
          cd scripts
          python3 deploy_evpn.py --inventory inventory.yaml
```

## Support and Resources

### Documentation
- [Cumulus Linux Documentation](https://docs.nvidia.com/networking-ethernet-software/cumulus-linux/)
- [EVPN Technical Guide](https://docs.nvidia.com/networking-ethernet-software/cumulus-linux/Layer-3/EVPN/)
- [FRR Documentation](https://docs.frrouting.org/)

### Community
- [Cumulus Networks Community](https://community.cumulusnetworks.com/)
- [GitHub Issues](https://github.com/ters-golemi/NVIDIA-VXLAN/issues)

### Getting Help
If you encounter issues:
1. Check this documentation
2. Review the troubleshooting section
3. Check switch logs: `/var/log/syslog` and `/var/log/frr/frr.log`
4. Open a GitHub issue with detailed error messages
