terraform {
  backend "gcs" {
    bucket = "a3146538e97419b7-terraform-remote-backend"
    prefix  = "terraform/state"
  }
}
