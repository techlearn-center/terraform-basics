#!/usr/bin/env python3
"""
Terraform LocalStack Dashboard
==============================
A visual web dashboard to see your AWS resources in LocalStack or real AWS.

Usage:
    python dashboard.py              # Open dashboard (LocalStack)
    python dashboard.py --aws        # Use real AWS credentials
    python dashboard.py --no-browser # Just start server
"""

import json
import subprocess
import sys
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
import argparse

# For Windows compatibility
if sys.platform == 'win32':
    os.system('color')
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

LOCALSTACK_ENDPOINT = "http://localhost:4566"
USE_AWS = False

# Colors for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_aws_command(service, action, extra_args=None):
    """Run an AWS CLI command against LocalStack or real AWS."""
    cmd = ["aws"]
    if not USE_AWS:
        cmd.extend(["--endpoint-url", LOCALSTACK_ENDPOINT])
    cmd.extend([service, action, "--output", "json"])
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else {}
        return None
    except Exception as e:
        return None


def get_vpcs():
    """Get VPCs created by Terraform (filter out default VPC)."""
    data = run_aws_command("ec2", "describe-vpcs")
    if not data:
        return []

    vpcs = []
    for vpc in data.get("Vpcs", []):
        # Skip default VPC
        if vpc.get("IsDefault", False):
            continue

        name = ""
        is_terraform = False
        for tag in vpc.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
            if tag["Key"] == "ManagedBy" and tag["Value"] == "terraform":
                is_terraform = True

        # Only include Terraform-managed or named VPCs
        if is_terraform or "terraform" in name.lower() or name:
            vpcs.append({
                "id": vpc["VpcId"],
                "cidr": vpc["CidrBlock"],
                "name": name or "(unnamed)",
                "state": vpc.get("State", "available")
            })
    return vpcs


def get_subnets(vpc_ids=None):
    """Get subnets (filter by VPC if provided)."""
    data = run_aws_command("ec2", "describe-subnets")
    if not data:
        return []

    subnets = []
    for subnet in data.get("Subnets", []):
        # Filter by VPC if specified
        if vpc_ids and subnet["VpcId"] not in vpc_ids:
            continue

        name = ""
        for tag in subnet.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
                break

        # Only include named subnets (Terraform adds names)
        if name:
            subnets.append({
                "id": subnet["SubnetId"],
                "vpc_id": subnet["VpcId"],
                "cidr": subnet["CidrBlock"],
                "az": subnet.get("AvailabilityZone", ""),
                "name": name
            })
    return subnets


def get_instances(vpc_ids=None):
    """Get EC2 instances (filter by VPC if provided)."""
    data = run_aws_command("ec2", "describe-instances")
    if not data:
        return []

    instances = []
    for reservation in data.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            # Filter by VPC if specified
            if vpc_ids and instance.get("VpcId") not in vpc_ids:
                continue

            name = ""
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                    break

            instances.append({
                "id": instance["InstanceId"],
                "type": instance.get("InstanceType", ""),
                "state": instance.get("State", {}).get("Name", "unknown"),
                "public_ip": instance.get("PublicIpAddress", ""),
                "private_ip": instance.get("PrivateIpAddress", ""),
                "subnet_id": instance.get("SubnetId", ""),
                "name": name or "(unnamed)"
            })
    return instances


def get_security_groups(vpc_ids=None):
    """Get security groups (filter by VPC, exclude default)."""
    data = run_aws_command("ec2", "describe-security-groups")
    if not data:
        return []

    sgs = []
    for sg in data.get("SecurityGroups", []):
        # Filter by VPC if specified
        if vpc_ids and sg.get("VpcId") not in vpc_ids:
            continue

        # Skip default security group
        if sg.get("GroupName") == "default":
            continue

        # Get ingress rules summary
        ingress_ports = []
        for rule in sg.get("IpPermissions", []):
            port = rule.get("FromPort", "all")
            if port != "all":
                ingress_ports.append(str(port))

        sgs.append({
            "id": sg["GroupId"],
            "name": sg.get("GroupName", ""),
            "description": sg.get("Description", ""),
            "vpc_id": sg.get("VpcId", ""),
            "ingress_ports": ingress_ports
        })
    return sgs


def get_internet_gateways(vpc_ids=None):
    """Get internet gateways (filter by VPC if provided)."""
    data = run_aws_command("ec2", "describe-internet-gateways")
    if not data:
        return []

    igws = []
    for igw in data.get("InternetGateways", []):
        vpc_id = ""
        for attachment in igw.get("Attachments", []):
            vpc_id = attachment.get("VpcId", "")

        # Filter by VPC if specified
        if vpc_ids and vpc_id not in vpc_ids:
            continue

        name = ""
        for tag in igw.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
                break

        if name or vpc_id:  # Only include if named or attached
            igws.append({
                "id": igw["InternetGatewayId"],
                "vpc_id": vpc_id,
                "name": name or "(unnamed)"
            })
    return igws


def generate_html():
    """Generate the dashboard HTML."""
    # Get VPCs first to filter other resources
    vpcs = get_vpcs()
    vpc_ids = [v["id"] for v in vpcs] if vpcs else None

    # Get filtered resources
    subnets = get_subnets(vpc_ids)
    instances = get_instances(vpc_ids)
    security_groups = get_security_groups(vpc_ids)
    internet_gateways = get_internet_gateways(vpc_ids)

    mode = "Real AWS" if USE_AWS else "LocalStack"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Dashboard - {mode}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }}

        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.85);
            backdrop-filter: blur(5px);
        }}
        .modal.active {{ display: flex; align-items: center; justify-content: center; }}
        .modal-content {{
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 16px;
            padding: 30px;
            max-width: 700px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            border: 1px solid rgba(0,217,255,0.2);
        }}
        .modal-close {{
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 28px;
            cursor: pointer;
            color: #888;
            transition: color 0.2s;
        }}
        .modal-close:hover {{ color: #fff; }}
        .modal-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #00d9ff;
        }}
        .modal-section {{
            margin-bottom: 20px;
        }}
        .modal-section h4 {{
            color: #00ff88;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .modal-section p {{
            line-height: 1.6;
            color: #ccc;
        }}
        .modal-section ul {{
            margin-left: 20px;
            line-height: 1.8;
            color: #ccc;
        }}
        .modal-section code {{
            background: rgba(0,217,255,0.2);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
            color: #00d9ff;
        }}
        .modal-diagram {{
            background: rgba(0,0,0,0.4);
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            white-space: pre;
            overflow-x: auto;
            font-size: 0.85em;
            line-height: 1.4;
            color: #00ff88;
        }}
        .modal-example {{
            background: rgba(0,217,255,0.1);
            border-left: 4px solid #00d9ff;
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin-top: 15px;
        }}
        .modal-example strong {{ color: #00d9ff; }}
        .modal-terraform {{
            background: rgba(0,0,0,0.4);
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            font-size: 0.85em;
            color: #feca57;
            margin-top: 10px;
        }}
        .modal-terraform .comment {{ color: #888; }}
        .modal-terraform .keyword {{ color: #ff6b6b; }}
        .modal-terraform .string {{ color: #00ff88; }}

        .section {{ cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }}
        .section:hover {{ transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,217,255,0.2); }}

        .header {{
            text-align: center;
            padding: 30px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header p {{ color: #888; font-size: 1.1em; }}
        .header .mode {{
            display: inline-block;
            background: {"#ff6b6b" if USE_AWS else "#00d9ff"};
            color: #1a1a2e;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px 40px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            color: #00d9ff;
        }}
        .stat-card .label {{ color: #888; margin-top: 5px; }}
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{
            color: #00d9ff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section h2 .icon {{ font-size: 1.5em; }}
        .resource-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }}
        .resource-card {{
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #00d9ff;
        }}
        .resource-card.vpc {{ border-left-color: #ff6b6b; }}
        .resource-card.subnet {{ border-left-color: #4ecdc4; }}
        .resource-card.instance {{ border-left-color: #45b7d1; }}
        .resource-card.sg {{ border-left-color: #96ceb4; }}
        .resource-card.igw {{ border-left-color: #feca57; }}
        .resource-card h3 {{
            color: #fff;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .resource-card .id {{
            font-family: monospace;
            color: #888;
            font-size: 0.85em;
            word-break: break-all;
        }}
        .resource-card .details {{
            margin-top: 10px;
            font-size: 0.9em;
        }}
        .resource-card .details span {{
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
        }}
        .status-running {{ color: #00ff88; }}
        .status-available {{ color: #00ff88; }}
        .empty-state {{
            text-align: center;
            color: #666;
            padding: 40px;
        }}
        .architecture {{
            background: rgba(0,0,0,0.4);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
            font-family: monospace;
            white-space: pre;
            overflow-x: auto;
            line-height: 1.8;
            color: #00d9ff;
            font-size: 14px;
        }}
        .refresh-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #00d9ff;
            color: #1a1a2e;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1em;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,217,255,0.3);
        }}
        .refresh-btn:hover {{ background: #00ff88; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Terraform Infrastructure Dashboard</h1>
        <p>Your AWS infrastructure visualization</p>
        <span class="mode">{mode}</span>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="number">{len(vpcs)}</div>
            <div class="label">VPCs</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(subnets)}</div>
            <div class="label">Subnets</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(instances)}</div>
            <div class="label">EC2 Instances</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(security_groups)}</div>
            <div class="label">Security Groups</div>
        </div>
    </div>
"""

    # Architecture diagram
    if vpcs:
        vpc = vpcs[0]
        subnet = subnets[0] if subnets else {"cidr": "10.0.1.0/24", "name": "Public Subnet", "id": "subnet-xxx"}
        instance = instances[0] if instances else None
        igw = internet_gateways[0] if internet_gateways else {"id": "igw-xxx"}
        sg = security_groups[0] if security_groups else {"name": "web-sg", "id": "sg-xxx", "ingress_ports": ["22", "80"]}

        instance_block = ""
        if instance:
            instance_block = f"""
    |   |   |   +---------------------------------------------+   |   |
    |   |   |   |  EC2: {instance['name'][:30]:<30}  |   |   |
    |   |   |   |  {instance['id']}               |   |   |
    |   |   |   |  Type: {instance['type']}  State: {instance['state']:<10}   |   |   |
    |   |   |   |  IP: {instance['public_ip'] or instance['private_ip'] or 'pending':<20}            |   |   |
    |   |   |   +---------------------------------------------+   |   |"""
        else:
            instance_block = """
    |   |   |              (No EC2 instances yet)                 |   |"""

        sg_rules = ", ".join(sg.get("ingress_ports", ["22", "80"])[:4]) if sg else "22, 80"

        html += f"""
    <div class="architecture">
                              +------------------+
                              |    INTERNET      |
                              +--------+---------+
                                       |
                              +--------v---------+
                              | Internet Gateway |
                              | {igw['id'][:20]:<20} |
                              +--------+---------+
                                       |
    +----------------------------------v----------------------------------+
    |  VPC: {vpc['name'][:40]:<40}             |
    |  {vpc['id']}   CIDR: {vpc['cidr']:<18}            |
    |                                                                     |
    |   +-------------------------------------------------------------+   |
    |   |  Subnet: {subnet['name'][:40]:<40}       |   |
    |   |  {subnet['id']}   CIDR: {subnet['cidr']:<15}    |   |
    |   |                                                             |   |{instance_block}
    |   |                                                             |   |
    |   +-------------------------------------------------------------+   |
    |                                                                     |
    |   +-------------------------+                                       |
    |   | Security Group          |   Inbound Rules:                      |
    |   | {sg['name'][:23]:<23} |   Ports: {sg_rules:<20}     |
    |   | {sg['id']:<23} |                                       |
    |   +-------------------------+                                       |
    +---------------------------------------------------------------------+
    </div>
"""

    # VPCs section
    html += """
    <div class="section" onclick="showModal('vpc')">
        <h2><span class="icon">🌐</span> VPCs <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if vpcs:
        for vpc in vpcs:
            html += f"""
            <div class="resource-card vpc">
                <h3>{vpc['name']}</h3>
                <div class="id">{vpc['id']}</div>
                <div class="details">
                    <span>CIDR: {vpc['cidr']}</span>
                    <span class="status-{vpc['state']}">{vpc['state']}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No VPCs found. Run terraform apply!</div>'

    html += """
        </div>
    </div>
"""

    # Subnets section
    html += """
    <div class="section" onclick="showModal('subnet')">
        <h2><span class="icon">📦</span> Subnets <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if subnets:
        for subnet in subnets:
            html += f"""
            <div class="resource-card subnet">
                <h3>{subnet['name']}</h3>
                <div class="id">{subnet['id']}</div>
                <div class="details">
                    <span>CIDR: {subnet['cidr']}</span>
                    <span>AZ: {subnet['az']}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No subnets found</div>'

    html += """
        </div>
    </div>
"""

    # EC2 Instances section
    html += """
    <div class="section" onclick="showModal('ec2')">
        <h2><span class="icon">💻</span> EC2 Instances <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if instances:
        for instance in instances:
            html += f"""
            <div class="resource-card instance">
                <h3>{instance['name']}</h3>
                <div class="id">{instance['id']}</div>
                <div class="details">
                    <span>{instance['type']}</span>
                    <span class="status-{instance['state']}">{instance['state']}</span>
                    <span>IP: {instance['public_ip'] or instance['private_ip'] or 'N/A'}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No EC2 instances found</div>'

    html += """
        </div>
    </div>
"""

    # Security Groups section
    html += """
    <div class="section" onclick="showModal('securitygroup')">
        <h2><span class="icon">🔒</span> Security Groups <span style="font-size:0.5em;color:#888;margin-left:10px;">Click to learn more</span></h2>
        <div class="resource-grid">
"""
    if security_groups:
        for sg in security_groups:
            ports = ", ".join(sg.get("ingress_ports", [])) or "No inbound rules"
            html += f"""
            <div class="resource-card sg">
                <h3>{sg['name']}</h3>
                <div class="id">{sg['id']}</div>
                <div class="details">
                    <span>Ports: {ports}</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No security groups found</div>'

    html += """
        </div>
    </div>

    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>

    <!-- Modal Container -->
    <div id="modal" class="modal" onclick="if(event.target===this)closeModal()">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal()">&times;</span>
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        const explanations = {
            vpc: {
                title: '🌐 Virtual Private Cloud (VPC)',
                content: `
                    <div class="modal-section">
                        <h4>What is a VPC?</h4>
                        <p>A VPC (Virtual Private Cloud) is your own private, isolated section of the AWS cloud. Think of it as your own private data center within AWS where you have complete control over the network.</p>
                    </div>
                    <div class="modal-section">
                        <h4>Key Concepts</h4>
                        <ul>
                            <li><strong>CIDR Block</strong> - The IP address range (e.g., <code>10.0.0.0/16</code> gives you 65,536 IPs)</li>
                            <li><strong>Region-specific</strong> - A VPC exists in one AWS region but spans all AZs</li>
                            <li><strong>Isolation</strong> - Resources in one VPC can't communicate with another by default</li>
                            <li><strong>Default VPC</strong> - AWS creates one per region, but production uses custom VPCs</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>VPC Components</h4>
                        <div class="modal-diagram">VPC (10.0.0.0/16)
├── Subnets (smaller IP ranges)
├── Route Tables (traffic rules)
├── Internet Gateway (internet access)
├── NAT Gateway (private subnet internet)
├── Security Groups (instance firewalls)
└── Network ACLs (subnet firewalls)</div>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "my-vpc"
  }
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Real-world analogy:</strong> A VPC is like renting a floor in an office building. You get your own space, control who enters (security groups), and set up your own rooms (subnets), but you're still in AWS's building (region).
                    </div>
                `
            },
            subnet: {
                title: '📦 Subnets',
                content: `
                    <div class="modal-section">
                        <h4>What is a Subnet?</h4>
                        <p>A subnet is a segment of your VPC's IP range where you place AWS resources. Subnets live in a single Availability Zone and can be either public (internet-accessible) or private (internal only).</p>
                    </div>
                    <div class="modal-section">
                        <h4>Public vs Private Subnets</h4>
                        <div class="modal-diagram">PUBLIC SUBNET                    PRIVATE SUBNET
├── Has route to IGW             ├── No direct internet route
├── Resources get public IPs     ├── Uses NAT for outbound
├── Web servers, load balancers  ├── Databases, app servers
└── Direct internet access       └── More secure</div>
                    </div>
                    <div class="modal-section">
                        <h4>CIDR Subnetting</h4>
                        <ul>
                            <li><code>10.0.0.0/16</code> - VPC with 65,536 IPs</li>
                            <li><code>10.0.1.0/24</code> - Subnet with 256 IPs (251 usable)</li>
                            <li><code>10.0.2.0/24</code> - Another subnet, same VPC</li>
                            <li>AWS reserves 5 IPs per subnet (first 4 + last 1)</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true  # Makes it public

  tags = {
    Name = "public-subnet"
  }
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Real-world analogy:</strong> Subnets are like rooms in your office floor (VPC). The reception area (public subnet) is where visitors enter, while the server room (private subnet) is locked away from public access.
                    </div>
                `
            },
            ec2: {
                title: '💻 EC2 Instances',
                content: `
                    <div class="modal-section">
                        <h4>What is EC2?</h4>
                        <p>EC2 (Elastic Compute Cloud) provides virtual servers in the cloud. You can launch instances of various sizes, install software, and run applications - just like physical servers but on-demand.</p>
                    </div>
                    <div class="modal-section">
                        <h4>Instance Types</h4>
                        <ul>
                            <li><strong>t2.micro</strong> - Free tier, 1 vCPU, 1GB RAM (testing)</li>
                            <li><strong>t3.medium</strong> - 2 vCPU, 4GB RAM (small apps)</li>
                            <li><strong>m5.large</strong> - 2 vCPU, 8GB RAM (general purpose)</li>
                            <li><strong>c5.xlarge</strong> - 4 vCPU, 8GB RAM (compute-intensive)</li>
                            <li><strong>r5.large</strong> - 2 vCPU, 16GB RAM (memory-intensive)</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Instance Lifecycle</h4>
                        <div class="modal-diagram">pending → running → stopping → stopped
                    ↓
              shutting-down → terminated

States:
• running    = You're paying, it's working
• stopped    = No compute charges, EBS still costs
• terminated = Gone forever (can't recover)</div>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "aws_instance" "web" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t2.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
    #!/bin/bash
    yum install -y httpd
    systemctl start httpd
  EOF

  tags = {
    Name = "web-server"
  }
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Real-world analogy:</strong> EC2 is like renting computers by the hour. Need a powerful machine for a few hours? Rent it. Need 100 servers for Black Friday? Spin them up, then shut them down when traffic drops.
                    </div>
                `
            },
            securitygroup: {
                title: '🔒 Security Groups',
                content: `
                    <div class="modal-section">
                        <h4>What is a Security Group?</h4>
                        <p>A Security Group is a virtual firewall that controls inbound and outbound traffic for your AWS resources. It's stateful - if you allow inbound traffic, the response is automatically allowed out.</p>
                    </div>
                    <div class="modal-section">
                        <h4>Key Rules</h4>
                        <ul>
                            <li><strong>Default DENY</strong> - All inbound traffic blocked by default</li>
                            <li><strong>Default ALLOW</strong> - All outbound traffic allowed by default</li>
                            <li><strong>Stateful</strong> - Return traffic is automatically allowed</li>
                            <li><strong>No DENY rules</strong> - You can only ALLOW; use NACLs for denies</li>
                        </ul>
                    </div>
                    <div class="modal-section">
                        <h4>Common Port Rules</h4>
                        <div class="modal-diagram">Port 22   (SSH)   - Remote server access
Port 80   (HTTP)  - Web traffic
Port 443  (HTTPS) - Secure web traffic
Port 3306 (MySQL) - Database
Port 5432 (PostgreSQL) - Database
Port 3389 (RDP)   - Windows remote desktop

Example rules:
• Allow SSH from your IP only: 22 from 1.2.3.4/32
• Allow HTTP from anywhere: 80 from 0.0.0.0/0
• Allow MySQL from app tier: 3306 from sg-app</div>
                    </div>
                    <div class="modal-section">
                        <h4>Terraform Example</h4>
                        <div class="modal-terraform">resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Allow web traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["YOUR_IP/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}</div>
                    </div>
                    <div class="modal-example">
                        <strong>Real-world analogy:</strong> Security Groups are like bouncers at a club. They check the guest list (rules) and only let in people who match the criteria (allowed ports/IPs). If you're already inside, you can leave freely (stateful).
                    </div>
                `
            }
        };

        function showModal(type) {
            const modal = document.getElementById('modal');
            const body = document.getElementById('modal-body');
            const data = explanations[type];
            if (data) {
                body.innerHTML = `<div class="modal-title">${data.title}</div>${data.content}`;
                modal.classList.add('active');
            }
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
    </script>
</body>
</html>
"""
    return html


def check_localstack():
    """Check if LocalStack is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", f"{LOCALSTACK_ENDPOINT}/_localstack/health"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except:
        return False


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = generate_html()
            self.wfile.write(html.encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logging


def main():
    global USE_AWS

    parser = argparse.ArgumentParser(description="Terraform Infrastructure Dashboard")
    parser.add_argument("--aws", action="store_true", help="Use real AWS instead of LocalStack")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    USE_AWS = args.aws

    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  Terraform Infrastructure Dashboard{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    if USE_AWS:
        print(f"  Mode: {Colors.YELLOW}Real AWS{Colors.END}")
        print(f"  Checking AWS credentials... ", end="")
        if not check_aws_credentials():
            print(f"{Colors.RED}NOT CONFIGURED{Colors.END}")
            print(f"\n  {Colors.YELLOW}Configure AWS credentials first:{Colors.END}")
            print(f"  aws configure")
            print(f"  # Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY\n")
            sys.exit(1)
        print(f"{Colors.GREEN}OK{Colors.END}")
    else:
        print(f"  Mode: {Colors.CYAN}LocalStack{Colors.END}")
        print(f"  Checking LocalStack... ", end="")
        if not check_localstack():
            print(f"{Colors.RED}NOT RUNNING{Colors.END}")
            print(f"\n  {Colors.YELLOW}Start LocalStack first:{Colors.END}")
            print(f"  docker-compose up -d\n")
            sys.exit(1)
        print(f"{Colors.GREEN}OK{Colors.END}")

    # Start server
    port = 8080
    server = HTTPServer(("localhost", port), DashboardHandler)

    print(f"\n  {Colors.GREEN}Dashboard running at:{Colors.END}")
    print(f"  {Colors.BOLD}http://localhost:{port}{Colors.END}\n")
    print(f"  Press Ctrl+C to stop.\n")

    # Open browser
    if not args.no_browser:
        def open_browser():
            time.sleep(1)
            webbrowser.open(f"http://localhost:{port}")
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.YELLOW}Dashboard stopped.{Colors.END}\n")
        server.shutdown()


if __name__ == "__main__":
    main()
