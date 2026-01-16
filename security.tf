# Security Group Configuration - STARTER FILE
# ============================================
# TODO: Create security group with proper rules!
#
# Requirements:
# - Allow SSH (port 22) inbound
# - Allow HTTP (port 80) inbound
# - Allow HTTPS (port 443) inbound
# - Allow all outbound traffic
#
# See README.md Step 4 for guidance!

# TODO: Create Security Group
# resource "aws_security_group" "web" {
#   name        = "${var.project_name}-web-sg"
#   description = "Security group for web server"
#   vpc_id      = aws_vpc.main.id
#
#   # SSH
#   ingress {
#     description = "SSH"
#     from_port   = 22
#     to_port     = 22
#     protocol    = "tcp"
#     cidr_blocks = var.allowed_ssh_cidr
#   }
#
#   # HTTP
#   ingress {
#     description = "HTTP"
#     from_port   = 80
#     to_port     = 80
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   # HTTPS
#   ingress {
#     description = "HTTPS"
#     from_port   = 443
#     to_port     = 443
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   # All outbound
#   egress {
#     description = "All outbound"
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   tags = {
#     Name = "${var.project_name}-web-sg"
#   }
# }
