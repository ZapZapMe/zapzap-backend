data "google_compute_network" "default_vpc" {
  name    = "default"
}

# create an vpc access connector
resource "google_vpc_access_connector" "vpc_access_connector" {
  provider = google-beta
  min_instances = 2
  max_instances = 10
  name     = "vpc-access-connector"
  network  = data.google_compute_network.default_vpc.name
  region   = var.gcp_region
  project = var.gcp_project_id
  ip_cidr_range = var.vpc_access_connector_ip_cidr_range
}


resource "google_compute_global_address" "private_ip_allocation" {
  name          = "friedaishot"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 24
  network       = data.google_compute_network.default_vpc.self_link
}