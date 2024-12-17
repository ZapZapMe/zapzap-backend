variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
  default = "zapzap01"  
}
variable "gcp_region" {
  description = "GCP region"
  type        = string
  default = "europe-west1"
}

variable "backend_domain" {
  description = "Backend domain"
  type        = string
  default = "api.zap-zap.me"
}

variable "frontend_domain" {
  description = "Frontend domain"
  type        = string
  default = "zap-zap.me"
}
