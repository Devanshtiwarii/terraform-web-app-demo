resource "google_artifact_registry_repository" "image_app" {
  location      = var.region
  repository_id = "image-app-repo"
  description   = "Docker repository for image management app"
  format        = "DOCKER"

  depends_on = [
    google_project_service.required
  ]
}