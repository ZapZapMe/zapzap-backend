
# resource "google_artifact_registry_repository" "zapzap_repo" {
#   repository_id = "zapzap-repo"
#   location      = var.gcp_region
#   format        = "DOCKER"
#   cleanup_policies {
#     id     = "keep-recent"
#     action = "KEEP"
#     most_recent_versions {
#       keep_count = 5
#     }
#   }
# }

# resource "google_cloud_run_v2_service" "zapzap_backend" {
#   name     = "zapzap-backend"
#   location = var.gcp_region
#   template {
#     volumes {
#       name = "cloudsql"
#       cloud_sql_instance {
#         instances = ["${var.gcp_project_id}:${var.gcp_region}:${google_sql_database_instance.postgres_instance.name}"]
#       }
#     }
#     containers {
#       image = "europe-west1-docker.pkg.dev/${var.gcp_project_id}/zapzap-repo/zapzap-backend"

#       ports {
#         name           = "http1"
#         container_port = 2121
#       }
#       env {
#         name  = "DB_HOST"
#         value = google_sql_database_instance.postgres_instance.private_ip_address
#       }
#       env {
#         name  = "DB_PORT"
#         value = 5432
#       }
#       env {
#         name  = "DB_USER"
#         value = google_sql_user.db_user.name
#       }
#       env {
#         name  = "DB_PASSWORD"
#         value = data.google_secret_manager_secret_version.db_password.secret_data
#       }
#       env {
#         name  = "DB_NAME"
#         value = google_sql_database.zapzap_database.name
#       }
#       env {
#         name  = "TWITTER_CLIENT_ID"
#         value = data.google_secret_manager_secret_version.twitter_client_id.secret_data
#       }
#       env {
#         name  = "TWITTER_CLIENT_SECRET"
#         value = data.google_secret_manager_secret_version.twitter_client_secret.secret_data
#       }
#     }
#   }
#   depends_on = [google_artifact_registry_repository.zapzap_repo]

# }

# resource "google_cloud_run_domain_mapping" "api-uri" {
#   name     = var.backend_domain
#   location = var.gcp_region
#   metadata {
#     namespace = var.gcp_project_id
#   }
#   spec {
#     route_name = google_cloud_run_v2_service.zapzap_backend.name
#   }
# }

# # Allow unauthenticated users to connect to the service
# resource "google_cloud_run_service_iam_member" "run_all_users" {
#   service  = google_cloud_run_v2_service.zapzap_backend.name
#   location = google_cloud_run_v2_service.zapzap_backend.location
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }

# output "cloud_run_service_url" {
#   value = google_cloud_run_v2_service.zapzap_backend.uri
# }


# output "cloud_run_domain_mapping_url" {
#   value = google_cloud_run_domain_mapping.api-uri.name
# }
