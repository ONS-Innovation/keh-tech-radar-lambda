variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID"
  type        = string
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key"
  type        = string
}

variable "service_subdomain" {
  description = "Service subdomain"
  type        = string
  default     = "tech-radar"
}

variable "domain" {
  description = "Domain"
  type        = string
  default     = "sdp-dev"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "ecr_repository" {
  description = "Name of the ECR repository containing the Lambda image"
  type        = string
  default     = "sdp-dev-tech-radar-lambda"
}

variable "container_ver" {
  description = "Container tag"
  type        = string
  default     = "v0.0.1"

}

variable "source_bucket" {
  description = "Source S3 bucket name"
  type        = string
  default     = "sdp-dev-tech-audit-tool-api"
}

variable "source_key" {
  description = "Source JSON file key"
  type        = string
  default     = "new_project_data.json"
}

variable "destination_bucket" {
  description = "Destination S3 bucket name"
  type        = string
  default     = "sdp-dev-tech-radar"
}

variable "destination_key" {
  description = "Destination CSV file key"
  type        = string
  default     = "onsTechDataAdoption.csv"
}

variable "project_tag" {
  description = "Project"
  type        = string
  default     = "TRT"
}

variable "team_owner_tag" {
  description = "Team Owner"
  type        = string
  default     = "Knowledge Exchange Hub"
}

variable "business_owner_tag" {
  description = "Business Owner"
  type        = string
  default     = "DST"
}

variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "sdp-dev-tech-radar-lambda"
}

variable "cron_job_schedule" {
  description = "Cron job schedule"
  type        = string
  default     = "cron(0 10 * * ? *)"
}
