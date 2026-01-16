#!/usr/bin/env python3
"""
Terraform LocalStack Dashboard
==============================
A visual web dashboard to see your AWS resources in LocalStack.

Usage:
    python dashboard.py          # Open dashboard in browser
    python dashboard.py --no-browser  # Just start server
"""

import json
import subprocess
import sys
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

# For Windows compatibility
if sys.platform == 'win32':
    os.system('color')

LOCALSTACK_ENDPOINT = "http://localhost:4566"

# Colors for terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_aws_command(service, action, extra_args=None):
    """Run an AWS CLI command against LocalStack."""
    cmd = [
        "aws", "--endpoint-url", LOCALSTACK_ENDPOINT,
        service, action, "--output", "json"
    ]
    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout else {}
        return None
    except Exception as e:
        return None


def get_vpcs():
    """Get all VPCs."""
    data = run_aws_command("ec2", "describe-vpcs")
    if not data:
        return []

    vpcs = []
    for vpc in data.get("Vpcs", []):
        name = ""
        for tag in vpc.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
                break
        vpcs.append({
            "id": vpc["VpcId"],
            "cidr": vpc["CidrBlock"],
            "name": name or "(unnamed)",
            "state": vpc.get("State", "available")
        })
    return vpcs


def get_subnets():
    """Get all subnets."""
    data = run_aws_command("ec2", "describe-subnets")
    if not data:
        return []

    subnets = []
    for subnet in data.get("Subnets", []):
        name = ""
        for tag in subnet.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
                break
        subnets.append({
            "id": subnet["SubnetId"],
            "vpc_id": subnet["VpcId"],
            "cidr": subnet["CidrBlock"],
            "az": subnet.get("AvailabilityZone", ""),
            "name": name or "(unnamed)"
        })
    return subnets


def get_instances():
    """Get all EC2 instances."""
    data = run_aws_command("ec2", "describe-instances")
    if not data:
        return []

    instances = []
    for reservation in data.get("Reservations", []):
        for instance in reservation.get("Instances", []):
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
                "name": name or "(unnamed)"
            })
    return instances


def get_security_groups():
    """Get all security groups."""
    data = run_aws_command("ec2", "describe-security-groups")
    if not data:
        return []

    sgs = []
    for sg in data.get("SecurityGroups", []):
        sgs.append({
            "id": sg["GroupId"],
            "name": sg.get("GroupName", ""),
            "description": sg.get("Description", ""),
            "vpc_id": sg.get("VpcId", "")
        })
    return sgs


def get_internet_gateways():
    """Get all internet gateways."""
    data = run_aws_command("ec2", "describe-internet-gateways")
    if not data:
        return []

    igws = []
    for igw in data.get("InternetGateways", []):
        name = ""
        for tag in igw.get("Tags", []):
            if tag["Key"] == "Name":
                name = tag["Value"]
                break
        vpc_id = ""
        for attachment in igw.get("Attachments", []):
            vpc_id = attachment.get("VpcId", "")
        igws.append({
            "id": igw["InternetGatewayId"],
            "vpc_id": vpc_id,
            "name": name or "(unnamed)"
        })
    return igws


def generate_html():
    """Generate the dashboard HTML."""
    vpcs = get_vpcs()
    subnets = get_subnets()
    instances = get_instances()
    security_groups = get_security_groups()
    internet_gateways = get_internet_gateways()

    # Filter out default VPC
    vpcs = [v for v in vpcs if "terraform" in v["name"].lower() or v["cidr"] == "10.0.0.0/16"]

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform LocalStack Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 30px;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: #888; font-size: 1.1em; }
        .stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px 40px;
            text-align: center;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-card .number {
            font-size: 3em;
            font-weight: bold;
            color: #00d9ff;
        }
        .stat-card .label { color: #888; margin-top: 5px; }
        .section {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .section h2 {
            color: #00d9ff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section h2 .icon { font-size: 1.5em; }
        .resource-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        .resource-card {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #00d9ff;
        }
        .resource-card.vpc { border-left-color: #ff6b6b; }
        .resource-card.subnet { border-left-color: #4ecdc4; }
        .resource-card.instance { border-left-color: #45b7d1; }
        .resource-card.sg { border-left-color: #96ceb4; }
        .resource-card.igw { border-left-color: #feca57; }
        .resource-card h3 {
            color: #fff;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .resource-card .id {
            font-family: monospace;
            color: #888;
            font-size: 0.85em;
            word-break: break-all;
        }
        .resource-card .details {
            margin-top: 10px;
            font-size: 0.9em;
        }
        .resource-card .details span {
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 3px 8px;
            border-radius: 4px;
            margin: 2px;
        }
        .status-running { color: #00ff88; }
        .status-available { color: #00ff88; }
        .empty-state {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        .architecture {
            background: rgba(0,0,0,0.4);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 25px;
            font-family: monospace;
            white-space: pre;
            overflow-x: auto;
            line-height: 1.6;
            color: #00d9ff;
        }
        .refresh-btn {
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
        }
        .refresh-btn:hover { background: #00ff88; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Terraform LocalStack Dashboard</h1>
        <p>Your AWS infrastructure running locally</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="number">""" + str(len(vpcs)) + """</div>
            <div class="label">VPCs</div>
        </div>
        <div class="stat-card">
            <div class="number">""" + str(len(subnets)) + """</div>
            <div class="label">Subnets</div>
        </div>
        <div class="stat-card">
            <div class="number">""" + str(len(instances)) + """</div>
            <div class="label">EC2 Instances</div>
        </div>
        <div class="stat-card">
            <div class="number">""" + str(len(security_groups)) + """</div>
            <div class="label">Security Groups</div>
        </div>
    </div>
"""

    # Architecture diagram
    if vpcs and instances:
        html += """
    <div class="architecture">
                        ┌─────────────────────────────────────────────────────┐
                        │                    INTERNET                         │
                        └───────────────────────┬─────────────────────────────┘
                                                │
                        ┌───────────────────────▼─────────────────────────────┐
                        │              Internet Gateway                        │
                        │              """ + (internet_gateways[0]["id"] if internet_gateways else "igw-xxx") + """                │
                        └───────────────────────┬─────────────────────────────┘
                                                │
        ┌───────────────────────────────────────▼───────────────────────────────────────┐
        │                              VPC: """ + vpcs[0]["cidr"] + """                              │
        │                              """ + vpcs[0]["id"] + """                       │
        │                                                                               │
        │   ┌─────────────────────────────────────────────────────────────────────┐    │
        │   │                    Public Subnet: """ + (subnets[0]["cidr"] if subnets else "10.0.1.0/24") + """                     │    │
        │   │                                                                     │    │
        │   │   ┌─────────────────────────────────────────────────────────┐      │    │
        │   │   │  EC2 Instance: """ + (instances[0]["id"] if instances else "i-xxx") + """                    │      │    │
        │   │   │  Type: """ + (instances[0]["type"] if instances else "t2.micro") + """  |  State: """ + (instances[0]["state"] if instances else "running") + """                      │      │    │
        │   │   │  Public IP: """ + (instances[0]["public_ip"] if instances else "x.x.x.x") + """                                 │      │    │
        │   │   └─────────────────────────────────────────────────────────┘      │    │
        │   │                                                                     │    │
        │   └─────────────────────────────────────────────────────────────────────┘    │
        │                                                                               │
        └───────────────────────────────────────────────────────────────────────────────┘
    </div>
"""

    # VPCs section
    html += """
    <div class="section">
        <h2><span class="icon">🌐</span> VPCs</h2>
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
    <div class="section">
        <h2><span class="icon">📦</span> Subnets</h2>
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
    <div class="section">
        <h2><span class="icon">💻</span> EC2 Instances</h2>
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
    <div class="section">
        <h2><span class="icon">🔒</span> Security Groups</h2>
        <div class="resource-grid">
"""
    if security_groups:
        for sg in security_groups:
            html += f"""
            <div class="resource-card sg">
                <h3>{sg['name']}</h3>
                <div class="id">{sg['id']}</div>
                <div class="details">
                    <span>{sg['description'][:50]}...</span>
                </div>
            </div>
"""
    else:
        html += '<div class="empty-state">No security groups found</div>'

    html += """
        </div>
    </div>

    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
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
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  Terraform LocalStack Dashboard{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

    # Check LocalStack
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
    if "--no-browser" not in sys.argv:
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
