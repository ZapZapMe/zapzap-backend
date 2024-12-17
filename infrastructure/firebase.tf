# resource "google_firebase_web_app" "zapzap_frontend" {
#   provider     = google-beta
#   project      = var.gcp_project_id
#   display_name = "ZapZap Frontend"
# }

resource "google_firebase_hosting_site" "zapzap_frontend" {
  site_id  = "zapzap-frontend-site"
  provider = google-beta
  project  = var.gcp_project_id
#  app_id   = google_firebase_web_app.zapzap_frontend.app_id
}

# output "zapzap_frontend_url" {
#   value = google_firebase_hosting_site.zapzap_frontend.default_url
# }