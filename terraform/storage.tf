resource "google_storage_bucket" "images" {
  name     = "terraform-webapp-images-12345"
  location = "asia-south1"

  uniform_bucket_level_access = true
  
}