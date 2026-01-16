# EC2 Instance Configuration - STARTER FILE
# ==========================================
# TODO: Create an EC2 instance!
#
# Requirements:
# - Use Amazon Linux 2 AMI (use data source)
# - Use t2.micro instance type
# - Place in the public subnet
# - Attach the security group
# - Add user data to install web server
#
# See README.md Step 5 for guidance!

# TODO: Data source to find latest Amazon Linux 2 AMI
# data "aws_ami" "amazon_linux" {
#   most_recent = true
#   owners      = ["amazon"]
#
#   filter {
#     name   = "name"
#     values = ["amzn2-ami-hvm-*-x86_64-gp2"]
#   }
#
#   filter {
#     name   = "virtualization-type"
#     values = ["hvm"]
#   }
# }

# TODO: Create EC2 Instance
# resource "aws_instance" "web" {
#   ami                    = data.aws_ami.amazon_linux.id
#   instance_type          = var.instance_type
#   subnet_id              = aws_subnet.public.id
#   vpc_security_group_ids = [aws_security_group.web.id]
#
#   user_data = <<-EOF
#               #!/bin/bash
#               yum update -y
#               yum install -y httpd
#               systemctl start httpd
#               systemctl enable httpd
#               echo "<h1>Hello from Terraform!</h1>" > /var/www/html/index.html
#               EOF
#
#   tags = {
#     Name = "${var.project_name}-web-server"
#   }
# }
