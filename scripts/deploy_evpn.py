#!/usr/bin/env python3
"""
EVPN Spine-Leaf Configuration Deployment Script

This script automates the deployment of EVPN VXLAN configuration
to Cumulus Linux switches in a Spine-Leaf topology.

Usage:
    python3 deploy_evpn.py --inventory inventory.yaml [--dry-run]

Requirements:
    - Python 3.6+
    - paramiko (pip install paramiko)
    - PyYAML (pip install pyyaml)
"""

import argparse
import os
import sys
import yaml
import time
from pathlib import Path

try:
    import paramiko
except ImportError:
    print("Error: paramiko module not found. Install it using: pip install paramiko")
    sys.exit(1)


class SwitchConfigurator:
    """Handle configuration deployment to Cumulus Linux switches"""
    
    def __init__(self, hostname, username, password, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.ssh = None
        
    def connect(self):
        """Establish SSH connection to the switch"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30
            )
            print(f"✓ Connected to {self.hostname}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to {self.hostname}: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh:
            self.ssh.close()
            print(f"✓ Disconnected from {self.hostname}")
    
    def backup_config(self):
        """Backup existing configuration"""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            backup_cmds = [
                f"sudo cp /etc/network/interfaces /etc/network/interfaces.backup.{timestamp}",
                f"sudo cp /etc/frr/frr.conf /etc/frr/frr.conf.backup.{timestamp}",
                f"sudo cp /etc/hostname /etc/hostname.backup.{timestamp}"
            ]
            
            for cmd in backup_cmds:
                stdin, stdout, stderr = self.ssh.exec_command(cmd)
                if stdout.channel.recv_exit_status() != 0:
                    error = stderr.read().decode()
                    print(f"  Warning: Backup command failed: {error}")
            
            print(f"✓ Configuration backed up on {self.hostname}")
            return True
        except Exception as e:
            print(f"✗ Failed to backup configuration on {self.hostname}: {e}")
            return False
    
    def deploy_interfaces_config(self, config_content):
        """Deploy /etc/network/interfaces configuration"""
        try:
            # Extract interfaces configuration from the config file
            interfaces_section = self._extract_section(
                config_content, 
                "# /etc/network/interfaces",
                "# /etc/frr/frr.conf"
            )
            
            if not interfaces_section:
                print(f"  Warning: No interfaces configuration found")
                return False
            
            # Create temporary file with configuration
            temp_file = f"/tmp/interfaces.{time.time()}"
            sftp = self.ssh.open_sftp()
            with sftp.file(temp_file, 'w') as f:
                f.write(interfaces_section)
            sftp.close()
            
            # Copy to actual location
            cmd = f"sudo cp {temp_file} /etc/network/interfaces"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            if stdout.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                print(f"✗ Failed to deploy interfaces config: {error}")
                return False
            
            print(f"✓ Deployed interfaces configuration to {self.hostname}")
            return True
        except Exception as e:
            print(f"✗ Failed to deploy interfaces config to {self.hostname}: {e}")
            return False
    
    def deploy_frr_config(self, config_content):
        """Deploy /etc/frr/frr.conf configuration"""
        try:
            # Extract FRR configuration from the config file
            frr_section = self._extract_section(
                config_content,
                "# /etc/frr/frr.conf",
                None
            )
            
            if not frr_section:
                print(f"  Warning: No FRR configuration found")
                return False
            
            # Create temporary file with configuration
            temp_file = f"/tmp/frr.conf.{time.time()}"
            sftp = self.ssh.open_sftp()
            with sftp.file(temp_file, 'w') as f:
                f.write(frr_section)
            sftp.close()
            
            # Copy to actual location
            cmd = f"sudo cp {temp_file} /etc/frr/frr.conf"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            if stdout.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                print(f"✗ Failed to deploy FRR config: {error}")
                return False
            
            print(f"✓ Deployed FRR configuration to {self.hostname}")
            return True
        except Exception as e:
            print(f"✗ Failed to deploy FRR config to {self.hostname}: {e}")
            return False
    
    def set_hostname(self, hostname):
        """Set the switch hostname"""
        try:
            cmd = f"sudo hostnamectl set-hostname {hostname}"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            if stdout.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                print(f"✗ Failed to set hostname: {error}")
                return False
            
            print(f"✓ Set hostname to {hostname}")
            return True
        except Exception as e:
            print(f"✗ Failed to set hostname on {self.hostname}: {e}")
            return False
    
    def reload_networking(self):
        """Reload network configuration"""
        try:
            cmd = "sudo ifreload -a"
            stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=60)
            if stdout.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                print(f"✗ Failed to reload networking: {error}")
                return False
            
            print(f"✓ Reloaded networking on {self.hostname}")
            return True
        except Exception as e:
            print(f"✗ Failed to reload networking on {self.hostname}: {e}")
            return False
    
    def restart_frr(self):
        """Restart FRR service"""
        try:
            cmd = "sudo systemctl restart frr"
            stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=60)
            if stdout.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                print(f"✗ Failed to restart FRR: {error}")
                return False
            
            print(f"✓ Restarted FRR on {self.hostname}")
            return True
        except Exception as e:
            print(f"✗ Failed to restart FRR on {self.hostname}: {e}")
            return False
    
    def verify_bgp_status(self):
        """Verify BGP neighbor status"""
        try:
            cmd = "sudo vtysh -c 'show bgp summary'"
            stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=30)
            output = stdout.read().decode()
            
            print(f"\n--- BGP Summary on {self.hostname} ---")
            print(output)
            return True
        except Exception as e:
            print(f"✗ Failed to verify BGP status on {self.hostname}: {e}")
            return False
    
    def verify_evpn_status(self):
        """Verify EVPN status"""
        try:
            cmd = "sudo vtysh -c 'show bgp l2vpn evpn summary'"
            stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=30)
            output = stdout.read().decode()
            
            print(f"\n--- EVPN Summary on {self.hostname} ---")
            print(output)
            return True
        except Exception as e:
            print(f"✗ Failed to verify EVPN status on {self.hostname}: {e}")
            return False
    
    def _extract_section(self, content, start_marker, end_marker):
        """Extract a section from configuration content"""
        lines = content.split('\n')
        in_section = False
        section_lines = []
        
        for line in lines:
            if start_marker in line:
                in_section = True
                continue
            
            if end_marker and end_marker in line:
                in_section = False
                break
            
            if in_section and not line.startswith('#'):
                section_lines.append(line)
        
        return '\n'.join(section_lines)


def load_inventory(inventory_file):
    """Load switch inventory from YAML file"""
    try:
        with open(inventory_file, 'r') as f:
            inventory = yaml.safe_load(f)
        return inventory
    except Exception as e:
        print(f"✗ Failed to load inventory file: {e}")
        sys.exit(1)


def deploy_switch(switch_name, switch_config, config_dir, dry_run=False):
    """Deploy configuration to a single switch"""
    print(f"\n{'='*60}")
    print(f"Deploying configuration to {switch_name}")
    print(f"{'='*60}")
    
    # Load configuration file
    config_file = os.path.join(config_dir, switch_config['config_file'])
    
    if not os.path.exists(config_file):
        print(f"✗ Configuration file not found: {config_file}")
        return False
    
    with open(config_file, 'r') as f:
        config_content = f.read()
    
    if dry_run:
        print(f"[DRY RUN] Would deploy configuration from {config_file}")
        print(f"[DRY RUN] Target: {switch_config['hostname']}")
        return True
    
    # Initialize switch configurator
    switch = SwitchConfigurator(
        hostname=switch_config['hostname'],
        username=switch_config['username'],
        password=switch_config['password'],
        port=switch_config.get('port', 22)
    )
    
    # Connect to switch
    if not switch.connect():
        return False
    
    try:
        # Backup existing configuration
        if not switch.backup_config():
            print("  Warning: Failed to backup configuration")
        
        # Set hostname
        if not switch.set_hostname(switch_name):
            print("  Warning: Failed to set hostname")
        
        # Deploy configurations
        if not switch.deploy_interfaces_config(config_content):
            print("  Error: Failed to deploy interfaces configuration")
            return False
        
        if not switch.deploy_frr_config(config_content):
            print("  Error: Failed to deploy FRR configuration")
            return False
        
        # Reload services
        if not switch.reload_networking():
            print("  Error: Failed to reload networking")
            return False
        
        # Wait a bit for network to stabilize
        time.sleep(5)
        
        if not switch.restart_frr():
            print("  Error: Failed to restart FRR")
            return False
        
        # Wait for BGP to establish
        time.sleep(10)
        
        # Verify deployment
        switch.verify_bgp_status()
        switch.verify_evpn_status()
        
        print(f"\n✓ Successfully deployed configuration to {switch_name}")
        return True
        
    finally:
        switch.disconnect()


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Deploy EVPN configuration to Cumulus Linux switches'
    )
    parser.add_argument(
        '--inventory',
        required=True,
        help='Path to inventory YAML file'
    )
    parser.add_argument(
        '--config-dir',
        default='../configs',
        help='Directory containing configuration files (default: ../configs)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making changes'
    )
    parser.add_argument(
        '--switches',
        nargs='+',
        help='Specific switches to deploy (default: all)'
    )
    
    args = parser.parse_args()
    
    # Load inventory
    inventory = load_inventory(args.inventory)
    
    if not inventory or 'switches' not in inventory:
        print("✗ Invalid inventory file format")
        sys.exit(1)
    
    # Get config directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.abspath(os.path.join(script_dir, args.config_dir))
    
    if not os.path.exists(config_dir):
        print(f"✗ Configuration directory not found: {config_dir}")
        sys.exit(1)
    
    # Deploy to switches
    switches_to_deploy = args.switches if args.switches else inventory['switches'].keys()
    
    results = {}
    for switch_name in switches_to_deploy:
        if switch_name not in inventory['switches']:
            print(f"✗ Switch '{switch_name}' not found in inventory")
            continue
        
        switch_config = inventory['switches'][switch_name]
        success = deploy_switch(switch_name, switch_config, config_dir, args.dry_run)
        results[switch_name] = success
    
    # Print summary
    print(f"\n{'='*60}")
    print("Deployment Summary")
    print(f"{'='*60}")
    
    for switch_name, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{switch_name}: {status}")
    
    # Exit with appropriate code
    if all(results.values()):
        print("\n✓ All deployments completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Some deployments failed. Check the output above for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
