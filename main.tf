provider "google" {
  project = "tips-backend"
  region  = "europe-west1"
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

# resource "google_secret_manager_secret" "db_password_secret" {
#   secret_id = "db-password"
#   replication {
#     user_managed {
#       replicas {
#         location = "europe-west1"
#       }
#     }
#   }
# }

data "google_secret_manager_secret_version" "db_password_version" {
  secret  = "db-password"
  version = "latest"
}

resource "google_cloud_run_v2_service" "cloud_run_service" {
  name       = "cloud-run-service"
  location   = "europe-west1"
  depends_on = [google_project_service.enable_services["run.googleapis.com"]]
  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      env {
        name  = "DB_CONNECTION_STRING"
        value = "postgresql://dbuser:${data.google_secret_manager_secret_version.db_password_version.secret_data}@/defaultdb?host=/cloudsql/${google_sql_database_instance.postgres_instance.connection_name}"
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = "tips-backend"
      }
    }
  }
}

resource "google_sql_database_instance" "postgres_instance" {
  name             = "postgres-instance"
  database_version = "POSTGRES_14"
  depends_on       = [google_project_service.enable_services["sqladmin.googleapis.com"]]
  region           = "europe-west1"
  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true
    }
    availability_type = "ZONAL"
  }
}

resource "google_sql_database" "default_database" {
  name     = "defaultdb"
  instance = google_sql_database_instance.postgres_instance.name
}

resource "google_sql_user" "postgres_user" {
  name     = "dbuser"
  instance = google_sql_database_instance.postgres_instance.name
  password = data.google_secret_manager_secret_version.db_password_version.secret_data
}

# Allow unauthenticated users to invoke the service
resource "google_cloud_run_service_iam_member" "run_all_users" {
  service  = google_cloud_run_v2_service.cloud_run_service.name
  location = google_cloud_run_v2_service.cloud_run_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}


// Print the SQL connection string to the console
output "sql_connection_string" {
  value     = "postgresql://${google_sql_user.postgres_user.name}:${data.google_secret_manager_secret_version.db_password_version.secret_data}@${google_sql_database_instance.postgres_instance.public_ip_address}:5432/${google_sql_database.default_database.name}"
  sensitive = true
}

// Print the Cloud Run service URL to the console
output "cloud_run_service_url" {
  value = google_cloud_run_v2_service.cloud_run_service.uri
}
