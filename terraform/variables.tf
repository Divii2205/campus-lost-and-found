# settings you can change without editing the other files
# each one has a default value

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name used in tags"
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "lostfound-eks"
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version. null = the current AWS default (avoids paid extended support)"
  type        = string
  default     = null
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.30.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "One public subnet per availability zone (at least two for EKS)"
  type        = list(string)
  default     = ["10.30.1.0/24", "10.30.2.0/24"]
}

variable "node_instance_type" {
  description = "EC2 instance type for the worker nodes"
  type        = string
  default     = "t3.small"
}

variable "node_desired_size" {
  description = "Number of worker nodes"
  type        = number
  default     = 1
}
