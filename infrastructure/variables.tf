variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
  default     = "zapzap01"
}
variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "europe-west1"
}

variable "backend_domain" {
  description = "Backend domain"
  type        = string
  default     = "api.zap-zap.me"
}

variable "frontend_domain" {
  description = "Frontend domain"
  type        = string
  default     = "zap-zap.me"
}

variable "vpc_access_connector_ip_cidr_range" {
  description = "VPC access connector IP CIDR range"
  type        = string
  default     = "10.8.0.0/28"
}
