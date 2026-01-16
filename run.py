#!/usr/bin/env python3
"""
Terraform Challenge Runner
===========================
Run this script to check your Terraform files and see your progress.

Usage:
    python run.py           # Check all files
    python run.py --validate # Run terraform validate (requires terraform)
"""

import subprocess
import sys
import os
import re
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

# For Windows compatibility
if sys.platform == 'win32':
    os.system('color')
    # Fix Unicode encoding on Windows
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def print_header():
    """Print the challenge header."""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  🏗️  Terraform Basics Challenge{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")


def load_tf_content(file_path):
    """Load Terraform file content."""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None


def is_commented_out(content, pattern):
    """Check if a pattern exists and is NOT commented out."""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
        if pattern in line:
            return False  # Found uncommented
    return True  # All occurrences are commented


def check_main_tf(content):
    """Check main.tf for required elements."""
    checks = []
    points = 0
    max_points = 10

    if content is None:
        return [("main.tf exists", False, "File not found")], 0, max_points

    # Check terraform block
    if 'terraform {' in content and not is_commented_out(content, 'terraform {'):
        checks.append(("Terraform block", True, "Configured"))
        points += 2
    else:
        checks.append(("Terraform block", False, "Not configured or commented"))

    # Check required_providers
    if 'required_providers' in content and 'aws' in content and not is_commented_out(content, 'required_providers'):
        checks.append(("AWS provider defined", True, "hashicorp/aws"))
        points += 3
    else:
        checks.append(("AWS provider defined", False, "Missing or commented"))

    # Check provider block
    if 'provider "aws"' in content and not is_commented_out(content, 'provider "aws"'):
        checks.append(("Provider configured", True, "AWS provider"))
        points += 3
    else:
        checks.append(("Provider configured", False, "Missing or commented"))

    # Check default_tags
    if 'default_tags' in content:
        checks.append(("Default tags", True, "Configured"))
        points += 2
    else:
        checks.append(("Default tags", False, "Missing"))

    return checks, points, max_points


def check_vpc_tf(content):
    """Check vpc.tf for required elements."""
    checks = []
    points = 0
    max_points = 20

    if content is None:
        return [("vpc.tf exists", False, "File not found")], 0, max_points

    # Check VPC
    if 'resource "aws_vpc"' in content and not is_commented_out(content, 'resource "aws_vpc"'):
        checks.append(("VPC resource", True, "aws_vpc"))
        points += 5
    else:
        checks.append(("VPC resource", False, "Missing or commented"))

    # Check subnet
    if 'resource "aws_subnet"' in content and not is_commented_out(content, 'resource "aws_subnet"'):
        checks.append(("Subnet resource", True, "aws_subnet"))
        points += 5
    else:
        checks.append(("Subnet resource", False, "Missing or commented"))

    # Check internet gateway
    if 'resource "aws_internet_gateway"' in content and not is_commented_out(content, 'resource "aws_internet_gateway"'):
        checks.append(("Internet gateway", True, "aws_internet_gateway"))
        points += 4
    else:
        checks.append(("Internet gateway", False, "Missing or commented"))

    # Check route table
    if 'resource "aws_route_table"' in content and not is_commented_out(content, 'resource "aws_route_table"'):
        checks.append(("Route table", True, "aws_route_table"))
        points += 3
    else:
        checks.append(("Route table", False, "Missing or commented"))

    # Check route table association
    if 'resource "aws_route_table_association"' in content and not is_commented_out(content, 'resource "aws_route_table_association"'):
        checks.append(("Route association", True, "aws_route_table_association"))
        points += 3
    else:
        checks.append(("Route association", False, "Missing or commented"))

    return checks, points, max_points


def check_security_tf(content):
    """Check security.tf for required elements."""
    checks = []
    points = 0
    max_points = 20

    if content is None:
        return [("security.tf exists", False, "File not found")], 0, max_points

    # Check security group
    if 'resource "aws_security_group"' in content and not is_commented_out(content, 'resource "aws_security_group"'):
        checks.append(("Security group", True, "aws_security_group"))
        points += 5
    else:
        checks.append(("Security group", False, "Missing or commented"))

    # Check ingress rules
    ingress_count = content.count('ingress {') - content.count('# ingress {')
    if ingress_count >= 3:
        checks.append(("Ingress rules", True, f"{ingress_count} rules"))
        points += 10
    elif ingress_count > 0:
        checks.append(("Ingress rules", False, f"Only {ingress_count} rules (need 3)"))
        points += ingress_count * 3
    else:
        checks.append(("Ingress rules", False, "Missing"))

    # Check egress
    if 'egress {' in content and not is_commented_out(content, 'egress {'):
        checks.append(("Egress rule", True, "All outbound"))
        points += 5
    else:
        checks.append(("Egress rule", False, "Missing or commented"))

    return checks, points, max_points


def check_ec2_tf(content):
    """Check ec2.tf for required elements."""
    checks = []
    points = 0
    max_points = 25

    if content is None:
        return [("ec2.tf exists", False, "File not found")], 0, max_points

    # Check AMI data source
    if 'data "aws_ami"' in content and not is_commented_out(content, 'data "aws_ami"'):
        checks.append(("AMI data source", True, "aws_ami"))
        points += 5
    else:
        checks.append(("AMI data source", False, "Missing or commented"))

    # Check EC2 instance
    if 'resource "aws_instance"' in content and not is_commented_out(content, 'resource "aws_instance"'):
        checks.append(("EC2 instance", True, "aws_instance"))
        points += 10
    else:
        checks.append(("EC2 instance", False, "Missing or commented"))

    # Check user_data
    if 'user_data' in content and not is_commented_out(content, 'user_data'):
        checks.append(("User data", True, "Bootstrap script"))
        points += 5
    else:
        checks.append(("User data", False, "Missing or commented"))

    # Check security group reference
    if 'vpc_security_group_ids' in content and not is_commented_out(content, 'vpc_security_group_ids'):
        checks.append(("Security group ref", True, "Attached"))
        points += 5
    else:
        checks.append(("Security group ref", False, "Missing or commented"))

    return checks, points, max_points


def check_variables_tf(content):
    """Check variables.tf for required elements."""
    checks = []
    points = 0
    max_points = 15

    if content is None:
        return [("variables.tf exists", False, "File not found")], 0, max_points

    required_vars = [
        ('aws_region', 3),
        ('project_name', 2),
        ('vpc_cidr', 3),
        ('instance_type', 3),
        ('allowed_ssh_cidr', 2),
    ]

    for var_name, var_points in required_vars:
        pattern = f'variable "{var_name}"'
        if pattern in content and not is_commented_out(content, pattern):
            checks.append((f"var.{var_name}", True, "Defined"))
            points += var_points
        else:
            checks.append((f"var.{var_name}", False, "Missing or commented"))

    return checks, points, max_points


def check_outputs_tf(content):
    """Check outputs.tf for required elements."""
    checks = []
    points = 0
    max_points = 10

    if content is None:
        return [("outputs.tf exists", False, "File not found")], 0, max_points

    required_outputs = [
        ('vpc_id', 2),
        ('instance_id', 2),
        ('instance_public_ip', 3),
        ('website_url', 3),
    ]

    for output_name, output_points in required_outputs:
        pattern = f'output "{output_name}"'
        if pattern in content and not is_commented_out(content, pattern):
            checks.append((f"output.{output_name}", True, "Defined"))
            points += output_points
        else:
            checks.append((f"output.{output_name}", False, "Missing or commented"))

    return checks, points, max_points


def check_all_files():
    """Check all Terraform files."""
    print_header()
    print(f"  {Colors.BOLD}Checking your Terraform files...{Colors.END}\n")

    project_dir = Path(__file__).parent

    total_points = 0
    max_total = 0

    file_checks = [
        ("main.tf", "Provider Config", check_main_tf, 10),
        ("vpc.tf", "VPC & Networking", check_vpc_tf, 20),
        ("security.tf", "Security Group", check_security_tf, 20),
        ("ec2.tf", "EC2 Instance", check_ec2_tf, 25),
        ("variables.tf", "Variables", check_variables_tf, 15),
        ("outputs.tf", "Outputs", check_outputs_tf, 10),
    ]

    for filename, display_name, check_func, max_pts in file_checks:
        file_path = project_dir / filename
        content = load_tf_content(file_path)
        checks, points, max_points = check_func(content)

        total_points += points
        max_total += max_points

        # Print results
        status_icon = f"{Colors.GREEN}✅{Colors.END}" if points == max_points else f"{Colors.YELLOW}⏳{Colors.END}"
        print(f"  {status_icon} {Colors.BOLD}{display_name}{Colors.END} ({points}/{max_points} points)")

        for check_name, passed, detail in checks:
            icon = f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"
            detail_str = f" - {detail}" if detail else ""
            print(f"      {icon} {check_name}{detail_str}")

        print()

    # Progress bar
    progress_pct = int((total_points / max_total) * 100) if max_total > 0 else 0
    bar_filled = int(progress_pct / 5)
    bar_empty = 20 - bar_filled

    bar_color = Colors.GREEN if progress_pct >= 80 else Colors.YELLOW
    print(f"  {Colors.BOLD}Score:{Colors.END}")
    print(f"  {bar_color}{'█' * bar_filled}{'░' * bar_empty}{Colors.END} {total_points}/{max_total} points ({progress_pct}%)")

    if progress_pct == 100:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}🎉 All Terraform files complete!{Colors.END}")
        print(f"  {Colors.CYAN}Run 'terraform validate' to check syntax!{Colors.END}")
    elif progress_pct >= 80:
        print(f"\n  {Colors.GREEN}Almost there! Check the items marked with ✗{Colors.END}")
    else:
        print(f"\n  {Colors.CYAN}Keep going! See README.md for guidance.{Colors.END}")

    print()
    return progress_pct == 100


def run_terraform_validate():
    """Run terraform validate."""
    print_header()
    print(f"  {Colors.BOLD}Running terraform validate...{Colors.END}\n")

    # Check if terraform is installed
    try:
        result = subprocess.run(
            ["terraform", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"  {Colors.RED}❌ Terraform not found{Colors.END}")
            print(f"  {Colors.YELLOW}Install Terraform first (see README.md Step 0){Colors.END}\n")
            return
    except FileNotFoundError:
        print(f"  {Colors.RED}❌ Terraform not installed{Colors.END}")
        print(f"  {Colors.YELLOW}Install Terraform first (see README.md Step 0){Colors.END}\n")
        return

    project_dir = Path(__file__).parent

    # Initialize
    print(f"  {Colors.CYAN}Running terraform init...{Colors.END}")
    result = subprocess.run(
        ["terraform", "init", "-backend=false"],
        cwd=str(project_dir),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"  {Colors.RED}❌ terraform init failed{Colors.END}")
        print(result.stderr)
        return

    print(f"  {Colors.GREEN}✓ Initialized{Colors.END}\n")

    # Validate
    print(f"  {Colors.CYAN}Running terraform validate...{Colors.END}")
    result = subprocess.run(
        ["terraform", "validate"],
        cwd=str(project_dir),
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"  {Colors.GREEN}✅ Configuration is valid!{Colors.END}")
        print(result.stdout)
    else:
        print(f"  {Colors.RED}❌ Validation failed{Colors.END}")
        print(result.stderr)

    print()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Terraform Challenge Runner")
    parser.add_argument("--validate", action="store_true", help="Run terraform validate")

    args = parser.parse_args()

    os.chdir(Path(__file__).parent)

    if args.validate:
        run_terraform_validate()
    else:
        check_all_files()


if __name__ == "__main__":
    main()
