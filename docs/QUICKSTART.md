# Quick Start Guide

This guide will help you quickly deploy the EVPN Spine-Leaf configuration to your Cumulus Linux switches.

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Cumulus Linux switches (minimum 4 switches: 2 spines, 2 leafs)
- [ ] Switches are physically cabled according to topology
- [ ] Management network configured on all switches
- [ ] SSH access to all switches
- [ ] Python 3.6+ installed on your workstation
- [ ] Switch credentials (username and password)

## Step-by-Step Deployment

### Step 1: Clone Repository (2 minutes)

```bash
git clone https://github.com/ters-golemi/NVIDIA-VXLAN.git
cd NVIDIA-VXLAN
```

### Step 2: Install Dependencies (1 minute)

```bash
pip install -r scripts/requirements.txt
```

Verify installation:
```bash
python3 -c "import paramiko, yaml; print('Dependencies OK')"
```

### Step 3: Update Inventory File (5 minutes)

Edit the inventory file with your switch information:

```bash
cd scripts
vi inventory.yaml
```

Update these fields for each switch:
- `hostname`: Management IP address of the switch
- `username`: SSH username (typically 'cumulus')
- `password`: SSH password

Example:
```yaml
switches:
  spine-01:
    hostname: 192.168.100.11    # ← Change this
    username: cumulus            # ← Change if different
    password: YourPassword       # ← Change this
```

### Step 4: Verify Connectivity (2 minutes)

Test SSH access to each switch:

```bash
# Test spine-01
ssh cumulus@192.168.100.11 "hostname"

# Test spine-02
ssh cumulus@192.168.100.12 "hostname"

# Test leaf-01
ssh cumulus@192.168.100.21 "hostname"

# Test leaf-02
ssh cumulus@192.168.100.22 "hostname"
```

All commands should succeed without errors.

### Step 5: Dry Run (2 minutes)

Test the deployment without making changes:

```bash
python3 deploy_evpn.py --inventory inventory.yaml --dry-run
```

Expected output:
```
[DRY RUN] Would deploy configuration from ../configs/spine/spine-01.conf
[DRY RUN] Target: 192.168.100.11
...
```

### Step 6: Deploy to Spines First (5-10 minutes)

Deploy configuration to spine switches:

```bash
python3 deploy_evpn.py --inventory inventory.yaml --switches spine-01 spine-02
```

Monitor the output for any errors. Expected flow:
```
============================================================
Deploying configuration to spine-01
============================================================
✓ Connected to 192.168.100.11
✓ Configuration backed up
✓ Set hostname to spine-01
✓ Deployed interfaces configuration
✓ Deployed FRR configuration
✓ Reloaded networking
✓ Restarted FRR
✓ Successfully deployed configuration to spine-01
```

### Step 7: Deploy to Leafs (5-10 minutes)

After spines are stable (wait 2-3 minutes), deploy to leafs:

```bash
python3 deploy_evpn.py --inventory inventory.yaml --switches leaf-01 leaf-02
```

### Step 8: Verify Deployment (5 minutes)

Check BGP status on spine-01:

```bash
ssh cumulus@192.168.100.11 "sudo vtysh -c 'show bgp summary'"
```

Expected output:
- Both leaf neighbors should be in "Established" state
- Uptime should be increasing

Check EVPN status:

```bash
ssh cumulus@192.168.100.11 "sudo vtysh -c 'show bgp l2vpn evpn summary'"
```

Check on a leaf switch:

```bash
ssh cumulus@192.168.100.21 "sudo vtysh -c 'show bgp summary'"
ssh cumulus@192.168.100.21 "sudo vtysh -c 'show bgp l2vpn evpn route'"
```

## Verification Commands

### On Spine Switches

```bash
# BGP neighbors
sudo vtysh -c 'show bgp summary'

# EVPN neighbors
sudo vtysh -c 'show bgp l2vpn evpn summary'

# Interface status
sudo net show interface

# BGP routes
sudo vtysh -c 'show ip bgp'
```

### On Leaf Switches

```bash
# BGP neighbors (should see both spines)
sudo vtysh -c 'show bgp summary'

# EVPN routes
sudo vtysh -c 'show bgp l2vpn evpn route'

# VXLAN interfaces
ip -d link show type vxlan

# Bridge FDB (VXLAN tunnel endpoints)
sudo bridge fdb show | grep dst

# VLAN to VNI mapping
sudo bridge vlan show
```

## Success Indicators

Your deployment is successful if:

1. **BGP Sessions**: All BGP neighbors are "Established"
   - Each spine should have 2 neighbors (both leafs)
   - Each leaf should have 2 neighbors (both spines)

2. **EVPN Sessions**: All EVPN sessions are active
   - Should see same neighbor count in l2vpn evpn summary

3. **VXLAN Tunnels**: VXLAN interfaces are UP
   - Check with: `ip link show type vxlan`

4. **Routes**: EVPN routes are being advertised
   - Type-2 and Type-3 routes should be visible

## Troubleshooting Quick Fixes

### Issue: Cannot connect to switch

```bash
# Test connectivity
ping 192.168.100.11

# Test SSH
ssh -v cumulus@192.168.100.11
```

**Fix**: Verify management IP and SSH service.

### Issue: BGP not establishing

```bash
# On spine, check BGP configuration
sudo vtysh -c 'show run bgp'

# Check interface status
sudo net show interface
```

**Fix**: Verify physical connectivity and IP addresses.

### Issue: Script fails with authentication error

```bash
# Verify credentials
ssh cumulus@192.168.100.11
```

**Fix**: Update username/password in inventory.yaml.

### Issue: VXLAN tunnels not forming

```bash
# Check VXLAN config
ip -d link show type vxlan

# Check loopback is reachable
ping 10.0.0.21  # From another switch
```

**Fix**: Verify loopback addresses and BGP is advertising connected routes.

## Rollback Procedure

If you need to rollback changes:

```bash
# SSH to the switch
ssh cumulus@192.168.100.11

# List backups
ls -la /etc/network/interfaces.backup.*
ls -la /etc/frr/frr.conf.backup.*

# Restore from backup (use your timestamp)
sudo cp /etc/network/interfaces.backup.20240101-120000 /etc/network/interfaces
sudo cp /etc/frr/frr.conf.backup.20240101-120000 /etc/frr/frr.conf

# Apply changes
sudo ifreload -a
sudo systemctl restart frr
```

## Next Steps

After successful deployment:

1. **Test Connectivity**: Verify end-to-end connectivity between VLANs
2. **Add VLANs**: Extend configuration with additional VLANs/VNIs
3. **Connect Hosts**: Connect servers to leaf switches
4. **Monitor**: Set up monitoring for BGP/EVPN status
5. **Document**: Document any customizations you made

## Common Customizations

### Add a New VLAN/VNI

Edit leaf configuration files:

```bash
vi configs/leaf/leaf-01.conf
```

Add:
```
# VLAN 30
auto vlan30
iface vlan30
    address 192.168.30.1/24
    vlan-id 30
    vlan-raw-device bridge

# VNI 30
auto vni30
iface vni30
    vxlan-id 10030
    vxlan-local-tunnelip 10.0.0.21
    bridge-access 30
    bridge-learning off
    bridge-arp-nd-suppress on
```

Update bridge:
```
auto bridge
iface bridge
    bridge-ports vni10 vni20 vni30
    bridge-vids 10 20 30
```

Redeploy:
```bash
python3 deploy_evpn.py --inventory inventory.yaml --switches leaf-01 leaf-02
```

## Getting Help

- **Documentation**: See [AUTOMATION.md](AUTOMATION.md) for detailed guide
- **Topology**: See [TOPOLOGY.md](TOPOLOGY.md) for design details
- **Issues**: Open a GitHub issue with:
  - Error messages
  - Output from verification commands
  - Switch logs: `/var/log/syslog`, `/var/log/frr/frr.log`

## Time Estimates

| Task | Estimated Time |
|------|----------------|
| Clone repository | 2 minutes |
| Install dependencies | 1 minute |
| Update inventory | 5 minutes |
| Verify connectivity | 2 minutes |
| Dry run | 2 minutes |
| Deploy spines | 10 minutes |
| Deploy leafs | 10 minutes |
| Verification | 5 minutes |
| **Total** | **~40 minutes** |

## Lab Environment

If you don't have physical switches, you can test with:

- **GNS3**: Cumulus VX images
- **EVE-NG**: Virtual Cumulus switches
- **Vagrant**: Cumulus VX boxes

Example Vagrant setup:
```bash
# Download Cumulus VX box
vagrant box add CumulusCommunity/cumulus-vx

# Use with this repository
# (Vagrantfile not included, but can be created)
```

---

**Pro Tip**: Always deploy to spine switches first, then leaf switches. This ensures the route reflectors are ready before the leafs try to establish EVPN sessions.
