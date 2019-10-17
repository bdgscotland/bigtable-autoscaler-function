terraform {
  required_version = ">= 0.12.7"
  backend "gcs" {
    bucket  = "terraform-state"
    prefix  = "terraform-state-bts"
  }
}
