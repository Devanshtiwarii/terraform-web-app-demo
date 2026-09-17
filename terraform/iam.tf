resource "google_service_account" "image_app_run" {
  account_id   = "image-app-run"
  display_name = "Image App Cloud Run Service Account"

  depends_on = [
    google_project_service.required
  ]
}

resource "google_storage_bucket_iam_member" "image_app_storage" {
  bucket = google_storage_bucket.images.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.image_app_run.email}"
}

resource "google_project_iam_member" "image_app_cloudsql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.image_app_run.email}"
}