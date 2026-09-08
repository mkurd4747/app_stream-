variable "aws_region" {
  description = "AWS Region in which to create the learning deployment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name used for AWS resource tags and names."
  type        = string
  default     = "tit-stream-api"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "learning"
}

variable "instance_type" {
  description = "EC2 instance type. Review current AWS pricing before applying."
  type        = string
  default     = "t3.micro"
}

variable "allowed_cidr" {
  description = "Public client CIDR allowed to reach API port 8000, normally YOUR_PUBLIC_IP/32."
  type        = string

  validation {
    condition     = can(cidrhost(var.allowed_cidr, 0)) && var.allowed_cidr != "0.0.0.0/0"
    error_message = "allowed_cidr must be a valid restricted CIDR and cannot be 0.0.0.0/0."
  }
}

variable "docker_image" {
  description = "Public Docker Hub image deployed on EC2."
  type        = string
  default     = "mkurd47/tit-stream-api:1.0"
}
