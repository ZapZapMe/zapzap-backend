terraform {
  backend "gcs" {
    bucket = "zapzap-tf-state"
    prefix  = "terraform/state"
  }
}
