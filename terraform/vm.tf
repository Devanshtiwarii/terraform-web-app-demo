resource "google_compute_instance" "image_app" {
  name         = "image-app-vm"
  machine_type = "e2-micro"
  zone         = "asia-south1-a"

   service_account {
    email  = google_service_account.image_app_run.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 20
      type  = "pd-balanced"
    }
  }

  network_interface {
    network = "default"

    access_config {
      # Ephemeral public IP
    }
  }

  tags = ["image-app"]
}


resource "google_compute_firewall" "image_app_http" {
  name    = "image-app-allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5000"]
  }

  source_ranges = ["0.0.0.0/0"]

  target_tags = ["image-app"]
}
