variable "aws_region" {
  type        = string
  description = "AWS region for the demo instance and artifact bucket"
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR for the isolated demo VPC created by this module"
  default     = "10.42.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "Public subnet CIDR for the single demo instance"
  default     = "10.42.1.0/24"
}

variable "allowed_cidr" {
  type        = string
  description = "Single trusted client IPv4 CIDR allowed to open the dashboard (prefer a /32)"
  validation {
    condition     = can(cidrnetmask(var.allowed_cidr))
    error_message = "allowed_cidr must be a valid IPv4 CIDR."
  }
}

variable "instance_type" {
  type        = string
  description = "EC2 size for the demo-only Compose stack"
  default     = "t3.xlarge"
}

variable "root_disk_gb" {
  type        = number
  description = "Encrypted gp3 root volume size"
  default     = 100
}

variable "name_prefix" {
  type        = string
  description = "Short unique deployment prefix"
  default     = "fleetguard-demo"
}
