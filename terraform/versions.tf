# the terraform and aws provider versions this project needs
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# the aws login comes from the aws configure command on your computer and never from this repo
provider "aws" {
  region = var.aws_region

  # these tags are added to every aws resource
  default_tags {
    tags = {
      Project     = "campus-lost-and-found"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
