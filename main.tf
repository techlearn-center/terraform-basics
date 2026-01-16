# Terraform Configuration - STARTER FILE
# ======================================
# TODO: Complete this provider configuration!
#
# Requirements:
# - Configure Terraform version >= 1.0.0
# - Add AWS provider (hashicorp/aws, version ~> 5.0)
# - Set the region using var.aws_region
# - Add default tags for all resources
#
# See README.md Step 2 for guidance!

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    # TODO: Add AWS provider
    # Hint:
    # aws = {
    #   source  = "hashicorp/aws"
    #   version = "~> 5.0"
    # }
  }
}

# TODO: Configure the AWS provider
# Hint:
# provider "aws" {
#   region = var.aws_region
#
#   default_tags {
#     tags = {
#       Project     = var.project_name
#       Environment = var.environment
#       ManagedBy   = "terraform"
#     }
#   }
# }
