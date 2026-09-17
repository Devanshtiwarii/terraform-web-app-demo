resource "google_sql_database_instance" "image_app_db" {
  name             = "image-app-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
  }
}

resource "google_sql_database" "image_app" {
  name     = "imageapp"
  instance = google_sql_database_instance.image_app_db.name
}

resource "google_sql_user" "appuser" {
  name     = "appuser"
  instance = google_sql_database_instance.image_app_db.name
}