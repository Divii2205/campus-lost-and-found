terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Credentials come from `aws configure` (~/.aws/credentials) - never from this repo.
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "campus-lost-and-found"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
