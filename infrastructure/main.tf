provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

resource "google_project_service" "enable_services" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "secretmanager.googleapis.com",
    "compute.googleapis.com",
  ])
  service = each.key
}

# data "google_iam_policy" "admin" {
#   binding {
#     role = "roles/secretmanager.secretAccessor"
#     members = [
#       "user:simon@imaginator.com",
#     ]
#   }
# }

# resource "google_project_iam_binding" "serviceusage_admin" {
#   project = "zapzap01"
#   role    = "roles/serviceusage.serviceUsageAdmin"
#   members = [
#     "user:simon@imaginator.com"
#   ]
# }

# resource "google_project_iam_binding" "service_usage_viewer" {
#   project = "zapzap01"
#   role    = "roles/serviceusage.serviceUsageViewer"
#   members = [
#     "user:simon@imaginator.com"
#   ]
# }

