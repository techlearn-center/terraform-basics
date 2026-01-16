# Terraform Basics

> **What you'll create:** Define cloud infrastructure as code using Terraform - provision a VPC, subnet, security group, and EC2 instance on AWS (simulated locally).

---

## Quick Start

```bash
# 1. Fork and clone this repo

# 2. Install Terraform (see Step 0)

# 3. Complete the .tf files

# 4. Test locally
terraform init
terraform plan
terraform apply

# 5. Push and check your score!
git push origin main
```

---

## What is This Challenge?

Instead of clicking through cloud consoles to create servers, you write **code** that describes your infrastructure. This is called **Infrastructure as Code (IaC)**.

**Why IaC matters:**
- ✅ Reproducible (same infrastructure every time)
- ✅ Version controlled (track changes in git)
- ✅ Reviewable (PRs for infrastructure changes)
- ✅ Automated (CI/CD for infrastructure)

---

## Do I Need Prior Knowledge?

**You need:**
- ✅ Basic understanding of cloud concepts (servers, networks)
- ✅ Command line basics

**You don't need:**
- ❌ AWS account (we'll use local simulation)
- ❌ Prior Terraform experience

**You'll learn:**
- What Terraform is and how it works
- HCL (HashiCorp Configuration Language)
- Providers, resources, variables, outputs
- The Terraform workflow (init, plan, apply)

---

## What You'll Build

| File | What You Create | Points |
|------|-----------------|--------|
| `main.tf` | Provider configuration | 10 |
| `vpc.tf` | VPC and subnet | 20 |
| `security.tf` | Security group | 20 |
| `ec2.tf` | EC2 instance | 25 |
| `variables.tf` | Input variables | 15 |
| `outputs.tf` | Output values | 10 |

---

## Step 0: Install Terraform

> ⏱️ **Time:** 10-15 minutes (one-time setup)

### What is Terraform?

**Terraform** by HashiCorp is the most popular IaC tool. It works with:
- AWS, Azure, GCP (clouds)
- Kubernetes, Docker (containers)
- GitHub, Datadog (services)
- And 3000+ other providers!

### How Terraform Works

```
You write:           Terraform does:
┌─────────────┐      ┌─────────────────────┐
│  .tf files  │ ──→  │ Creates resources   │
│  (your code)│      │ in the right order  │
└─────────────┘      └─────────────────────┘

main.tf:
resource "aws_instance" "web" {
  ami           = "ami-12345"
  instance_type = "t2.micro"
}

           ↓ terraform apply

AWS creates an EC2 instance for you!
```

### Install Terraform

<details>
<summary>🪟 Windows</summary>

**Option 1: Chocolatey (Recommended)**
```powershell
choco install terraform
```

**Option 2: Manual Install**
1. Download from https://terraform.io/downloads
2. Extract the zip
3. Add to your PATH

**Verify:**
```bash
terraform --version
```

</details>

<details>
<summary>🍎 Mac</summary>

```bash
# Using Homebrew
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify
terraform --version
```

</details>

<details>
<summary>🐧 Linux</summary>

```bash
# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Verify
terraform --version
```

</details>

✅ **Checkpoint:** `terraform --version` shows the version

---

## Step 1: Understand Terraform Basics

> ⏱️ **Time:** 15-20 minutes (reading)

### HCL Syntax

Terraform uses **HCL (HashiCorp Configuration Language)**:

```hcl
# This is a comment

# Resource block - creates something
resource "aws_instance" "my_server" {
  ami           = "ami-12345"
  instance_type = "t2.micro"

  tags = {
    Name = "MyServer"
  }
}

# Variable - input value
variable "instance_type" {
  description = "EC2 instance type"
  default     = "t2.micro"
}

# Output - value to display/export
output "server_ip" {
  value = aws_instance.my_server.public_ip
}
```

### Key Concepts

| Concept | What It Is | Example |
|---------|-----------|---------|
| **Provider** | Cloud/service to use | `provider "aws" {}` |
| **Resource** | Thing to create | `resource "aws_instance" "web" {}` |
| **Variable** | Input parameter | `variable "region" {}` |
| **Output** | Exported value | `output "ip" { value = ... }` |
| **Data source** | Read existing data | `data "aws_ami" "latest" {}` |
| **Module** | Reusable code package | `module "vpc" {}` |

### The Terraform Workflow

```bash
terraform init      # Download providers
terraform plan      # Preview changes
terraform apply     # Make changes
terraform destroy   # Delete everything
```

---

## Step 2: Configure the Provider

> ⏱️ **Time:** 10-15 minutes

### What is a Provider?

A provider is a plugin that lets Terraform talk to a service (AWS, Azure, etc.).

### Your Task

Complete `main.tf`:

**Requirements:**
- [ ] Configure the AWS provider
- [ ] Set the region using a variable
- [ ] Add default tags

<details>
<summary>💡 Hint 1: Basic Provider</summary>

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}
```

</details>

<details>
<summary>💡 Hint 2: Using Variables</summary>

```hcl
provider "aws" {
  region = var.aws_region  # Reference a variable
}
```

</details>

<details>
<summary>🎯 Full Solution</summary>

```hcl
terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "terraform-challenge"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

</details>

---

## Step 3: Create a VPC and Subnet

> ⏱️ **Time:** 25-30 minutes

### What is a VPC?

A **Virtual Private Cloud (VPC)** is your own isolated network in the cloud. Think of it as your private data center.

```
VPC (10.0.0.0/16)
├── Public Subnet (10.0.1.0/24)  ← Internet accessible
│   └── Web servers
└── Private Subnet (10.0.2.0/24) ← Internal only
    └── Databases
```

### Your Task

Complete `vpc.tf`:

**Requirements:**
- [ ] Create a VPC with CIDR 10.0.0.0/16
- [ ] Create a public subnet (10.0.1.0/24)
- [ ] Create an internet gateway
- [ ] Create a route table with internet access

<details>
<summary>💡 Hint 1: VPC Resource</summary>

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "main-vpc"
  }
}
```

</details>

<details>
<summary>💡 Hint 2: Subnet</summary>

```hcl
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id  # Reference the VPC
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet"
  }
}
```

</details>

<details>
<summary>💡 Hint 3: Internet Gateway & Route Table</summary>

```hcl
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
```

</details>

<details>
<summary>🎯 Full Solution</summary>

```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Public Subnet
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
```

</details>

---

## Step 4: Create a Security Group

> ⏱️ **Time:** 20-25 minutes

### What is a Security Group?

A **Security Group** is a virtual firewall that controls traffic to your instances.

```
Inbound Rules (what can connect TO your server):
- Port 22 (SSH) from your IP
- Port 80 (HTTP) from anywhere
- Port 443 (HTTPS) from anywhere

Outbound Rules (what your server can connect TO):
- All traffic to anywhere (default)
```

### Your Task

Complete `security.tf`:

**Requirements:**
- [ ] Allow SSH (port 22) from anywhere (or your IP)
- [ ] Allow HTTP (port 80) from anywhere
- [ ] Allow HTTPS (port 443) from anywhere
- [ ] Allow all outbound traffic

<details>
<summary>💡 Hint 1: Security Group Structure</summary>

```hcl
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Security group for web server"
  vpc_id      = aws_vpc.main.id

  # Inbound rules go here

  # Outbound rules go here

  tags = {
    Name = "web-sg"
  }
}
```

</details>

<details>
<summary>💡 Hint 2: Ingress Rules</summary>

```hcl
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # In production, use your IP!
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
```

</details>

<details>
<summary>🎯 Full Solution</summary>

```hcl
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "Security group for web server"
  vpc_id      = aws_vpc.main.id

  # SSH
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidr
  }

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound
  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-web-sg"
  }
}
```

</details>

---

## Step 5: Create an EC2 Instance

> ⏱️ **Time:** 25-30 minutes

### What is an EC2 Instance?

**EC2 (Elastic Compute Cloud)** is a virtual server in AWS. You specify:
- AMI (Amazon Machine Image) - the OS
- Instance type - CPU/memory
- Security group - firewall rules
- Subnet - network location

### Your Task

Complete `ec2.tf`:

**Requirements:**
- [ ] Use Amazon Linux 2 AMI (or Ubuntu)
- [ ] Use t2.micro instance type
- [ ] Place in the public subnet
- [ ] Attach the security group
- [ ] Add a user data script to install a web server

<details>
<summary>💡 Hint 1: Finding the AMI</summary>

Use a data source to find the latest AMI:

```hcl
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}
```

Then reference it: `data.aws_ami.amazon_linux.id`

</details>

<details>
<summary>💡 Hint 2: EC2 Resource</summary>

```hcl
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  tags = {
    Name = "web-server"
  }
}
```

</details>

<details>
<summary>💡 Hint 3: User Data Script</summary>

User data runs on first boot:

```hcl
resource "aws_instance" "web" {
  # ... other config ...

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from Terraform!</h1>" > /var/www/html/index.html
              EOF
}
```

</details>

<details>
<summary>🎯 Full Solution</summary>

```hcl
# Find latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instance
resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y httpd
              systemctl start httpd
              systemctl enable httpd
              echo "<h1>Hello from Terraform!</h1>" > /var/www/html/index.html
              echo "<p>Instance ID: $(curl -s http://169.254.169.254/latest/meta-data/instance-id)</p>" >> /var/www/html/index.html
              EOF

  tags = {
    Name = "${var.project_name}-web-server"
  }
}
```

</details>

---

## Step 6: Add Variables and Outputs

> ⏱️ **Time:** 15-20 minutes

### Variables

Variables make your code reusable and configurable.

Complete `variables.tf`:

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "terraform-challenge"
}

variable "environment" {
  description = "Environment (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "allowed_ssh_cidr" {
  description = "CIDR blocks allowed for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # In production, restrict this!
}
```

### Outputs

Outputs display important values after apply.

Complete `outputs.tf`:

```hcl
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Public subnet ID"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.web.id
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.web.public_ip
}

output "website_url" {
  description = "Website URL"
  value       = "http://${aws_instance.web.public_ip}"
}
```

---

## Step 7: Test Your Configuration

### Validate Syntax

```bash
# Check for syntax errors
terraform validate
```

### Format Code

```bash
# Auto-format your code
terraform fmt
```

### Run the Progress Checker

```bash
python run.py
```

### (Optional) Test with LocalStack

If you want to actually run your Terraform locally without AWS:

```bash
# Start LocalStack (AWS simulator)
docker-compose up -d

# Initialize Terraform
terraform init

# Plan (preview)
terraform plan

# Apply (create resources)
terraform apply

# Destroy (cleanup)
terraform destroy
```

---

## Understanding Terraform (For DevOps Students)

### State Management

Terraform tracks what it creates in a **state file** (`terraform.tfstate`):

```
terraform.tfstate:
{
  "resources": [
    {
      "type": "aws_instance",
      "name": "web",
      "id": "i-1234567890"
    }
  ]
}
```

**Important:** In teams, store state remotely (S3, Terraform Cloud) to avoid conflicts!

### Terraform Commands

```bash
terraform init      # Initialize, download providers
terraform validate  # Check syntax
terraform fmt       # Format code
terraform plan      # Preview changes
terraform apply     # Make changes
terraform destroy   # Delete everything
terraform show      # Show current state
terraform output    # Show outputs
```

### What You Can Say in Interviews

> "I used Terraform to define AWS infrastructure as code, including a VPC with public subnet, security groups with proper ingress/egress rules, and an EC2 instance with user data for bootstrapping. I understand the Terraform workflow of init, plan, and apply, and the importance of state management. The infrastructure is version controlled and reproducible."

---

## Troubleshooting

<details>
<summary>❌ "Provider not found"</summary>

Run `terraform init` to download providers:
```bash
terraform init
```

</details>

<details>
<summary>❌ "Invalid reference"</summary>

Check resource names match. References use format:
- `aws_vpc.main.id` (resource type.name.attribute)
- `var.region` (variable reference)

</details>

<details>
<summary>❌ "CIDR block invalid"</summary>

CIDR format: `10.0.0.0/16`
- First part: IP address
- `/16`: Subnet mask (16 = 65,536 IPs)

</details>

<details>
<summary>❌ "Cycle detected"</summary>

You have circular dependencies. Resource A depends on B, and B depends on A.
Check your references and break the cycle.

</details>

---

## What You Learned

- ✅ **Infrastructure as Code** - Why and how
- ✅ **Terraform basics** - Providers, resources, variables, outputs
- ✅ **AWS networking** - VPCs, subnets, internet gateways
- ✅ **Security groups** - Firewall rules
- ✅ **EC2 instances** - Virtual servers
- ✅ **User data** - Bootstrap scripts
- ✅ **Terraform workflow** - Init, plan, apply, destroy

---

## Next Steps

- **2.2 AWS Deployment** - Deploy to real AWS
- **2.3 Kubernetes Basics** - Container orchestration

Good luck! 🏗️
