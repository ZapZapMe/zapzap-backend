resource "google_project_service" "sqladmin" {
  service = "sqladmin.googleapis.com"
}

# create a postgres database instance called postgres-instance
resource "google_sql_database_instance" "postgres_instance" {
  name             = "postgres-instance"
  database_version = "POSTGRES_15"
  region           = var.gcp_region
  deletion_protection = false
  project          = var.gcp_project_id
  settings {
    tier = "db-f1-micro"
    deletion_protection_enabled = true
    availability_type = "ZONAL"
  }
}

# create a database called zapzap
resource "google_sql_database" "database" {
  name     = "zapzap"
  instance = google_sql_database_instance.postgres_instance.name
}


resource "google_sql_user" "db_user" {
  name     = "db-user"
  instance = google_sql_database_instance.postgres_instance.name
  password = data.google_secret_manager_secret_version.db_password.secret_data
}

# password is setup using gcloud and exposed as a secret in TF

data "google_secret_manager_secret_version" "db_password" {
  secret  = "db_password"
  version = "latest"
}

output "db_password" {
  value     = data.google_secret_manager_secret_version.db_password.secret_data
  sensitive = true
}

# output "sql_connection_string" {
#   value     = "postgresql://${google_sql_user.postgres_user.name}:${data.google_secret_manager_secret_version.db_password.secret_data}@${google_sql_database_instance.postgres_instance.public_ip_address}:5432/${google_sql_database.default_database.name}"
#   sensitive = true
# }
