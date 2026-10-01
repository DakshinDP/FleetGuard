variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "service_name" {
  type    = string
  default = "fleetguard-api"
}

variable "container_image" {
  type        = string
  description = "Published FleetGuard container image URI"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnets in at least two AZs"
}

variable "security_group_ids" {
  type        = list(string)
  description = "Pre-created security groups allowing only trusted ingress and required egress"
}

variable "secret_arn" {
  type        = string
  description = "Secrets Manager JSON secret with POSTGRES_DSN, JWT_SECRET, DEMO_PASSWORD"
}

variable "clickhouse_host" {
  type = string
}

variable "redis_url" {
  type = string
}

variable "kafka_bootstrap_servers" {
  type = string
}

variable "desired_count" {
  type    = number
  default = 2
}
