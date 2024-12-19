resource "google_project_service" "sqladmin" {
  service = "sqladmin.googleapis.com"
}

# create a postgres database instance called postgres-instance
resource "google_sql_database_instance" "postgres_instance" {
  name                = "postgres-instance"
  database_version    = "POSTGRES_15"
  region              = var.gcp_region
  deletion_protection = false
  project             = var.gcp_project_id
  settings {
    ip_configuration {
      ipv4_enabled    = "false"
      private_network = google_compute_network.peering_network.id
    }
    tier                        = "db-f1-micro"
    deletion_protection_enabled = true
    availability_type           = "ZONAL"
  }
}


# create a database called zapzap
resource "google_sql_database" "zapzap_database" {
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

output zapzap_database {
  value = google_sql_database.zapzap_database.name
}