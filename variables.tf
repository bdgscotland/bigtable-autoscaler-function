variable "project_name" {
  description = "The project name"
  default = "google-project-name"
}

variable "project_id" {
  description = "The project ID if it differs from the name"
  default = "google-project-name-34939"
}

variable "job_schedule" {
  description = "The cron schedule for the BTS"
  default = "*/20 * * * *"
}

variable "function_entry_point" {
  description = "The entry point the GCF runs"
  default = "main"
}

variable "function_runtime" {
  default = "python37"
}

variable "region" {
  default = "us-central1"
}

variable "bts_bigtable_data" {
  default = <<EOF
{
  "bigtable": [
    {
      "name": "bigtable-instance",
      "cluster": "bigtable-instance-c1",
      "cpu": [
        {
          "high": 0.8,
          "low": 0.4
        }
      ],
      "nodes": [
        {
          "max": 15,
          "min": 3
        }
      ]
    }
  ]
}
EOF
}
