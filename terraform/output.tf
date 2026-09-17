output "project_id" {
  value = var.project_id
}

output "bucket_name" {
  value = google_storage_bucket.images.name
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.image_app.name
}

output "cloud_sql_connection_name" {
  value = google_sql_database_instance.image_app_db.connection_name
}
