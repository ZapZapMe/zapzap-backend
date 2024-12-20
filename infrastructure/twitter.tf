data "google_secret_manager_secret_version" "twitter_client_id" {
    secret  = "twitter_client_id"
    version = "latest"
}

data "google_secret_manager_secret_version" "twitter_client_secret" {
    secret  = "twitter_client_secret"
    version = "latest"
}
