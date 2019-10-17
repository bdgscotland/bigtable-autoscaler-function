# Bigtable Autoscaler v3

This modules makes it easy to set up Bigtable autoscalers

## Compatibility

This module is meant for use with Terraform 0.12.

## Usage
In variables, the JSON data for configuration of the autoscaler is like:

```hcl
Variable "bts_bigtable_data" {
  default = <<EOF
{
  "bigtable": [
    {
      "name": "bigtable-instance",
      "cluster": "bigtable-instance-c1",
      "cpu": [
        {
          "high": "0.7",
          "low": "0.5"
        }
      ],
      "nodes": [
        {
          "max": "15",
          "min": "3"
        }
      ]
    }
  ]
}
EOF
}
```


```hcl
module "bts_instance" {
  source                        = "git::ssh://git@github.com/terraform-google-modules/terraform-google-scheduled-function.git"
  project_id                    = var.project_id
  job_name                      = "bts_instance"
  job_schedule                  = var.job_schedule
  function_entry_point          = var.function_entry_point
  function_source_directory     = "bts"
  function_name                 = "bts_instance"
  function_runtime              = var.function_runtime
  function_timeout_s            = "61"
  function_available_memory_mb  = "128"
  region                        = var.region
  topic_name                    = "bts_instance_scheduler"
  message_data                  = base64encode(var.bts_instance_data)
}
```

Then perform the following commands on the root folder:

- `terraform init` to get the plugins
- `terraform plan` to see the infrastructure plan
- `terraform apply` to apply the infrastructure build
- `terraform destroy` to destroy the built infrastructure


## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|:----:|:-----:|:-----:|
| bucket\_name | The name to apply to the bucket. Will default to a string of <project-id>-scheduled-function-XXXX> with XXXX being random characters. | string | `""` | no |
| function\_available\_memory\_mb | The amount of memory in megabytes allotted for the function to use. | string | `"256"` | no |
| function\_description | The description of the function. | string | `"Processes log export events provided through a Pub/Sub topic subscription."` | no |
| function\_entry\_point | The name of a method in the function source which will be invoked when the function is executed. | string | n/a | yes |
| function\_environment\_variables | A set of key/value environment variable pairs to assign to the function. | map | `<map>` | no |
| function\_event\_trigger\_failure\_policy\_retry | A toggle to determine if the function should be retried on failure. | string | `"false"` | no |
| function\_labels | A set of key/value label pairs to assign to the function. | map | `<map>` | no |
| function\_name | The name to apply to the function | string | n/a | yes |
| function\_runtime | The runtime in which the function will be executed. | string | `"nodejs6"` | no |
| function\_source\_archive\_bucket\_labels | A set of key/value label pairs to assign to the function source archive bucket. | map | `<map>` | no |
| function\_source\_directory | The contents of this directory will be archived and used as the function source. | string | n/a | yes |
| function\_timeout\_s | The amount of time in seconds allotted for the execution of the function. | string | `"60"` | no |
| job\_description | Addition text to describet the job | string | `""` | no |
| job\_name | The name of the scheduled job to run | string | n/a | yes |
| job\_schedule | The job frequency, in cron syntax | string | `"*/2 * * * *"` | no |
| message\_data | The data to send in the topic message. | string | `"dGVzdA=="` | no |
| project\_id | The ID of the project where this VPC will be created | string | n/a | yes |
| region | The region in which resources will be applied. | string | n/a | yes |
| topic\_name | Name of pubsub topic connecting the scheduled job and the function | string | `"test-topic"` | no |
| time\_zone | The timezone to be used in scheduler job | string | `"Etc/UTC"` | no |

## Outputs

| Name | Description |
|------|-------------|
| name | The name of the job created |


## Requirements
### Terraform plugins
- [Terraform](https://www.terraform.io/downloads.html) 0.12.x
- [terraform-provider-google](https://github.com/terraform-providers/terraform-provider-google) plugin v2.1


### App Engine
Note that this module requires App Engine being configured in the specified project/region.
This is because Google Cloud Scheduler is dependent on the project being configured with App Engine.
Refer to the [Google Cloud Scheduler documentation](https://cloud.google.com/scheduler/docs/) for more
information on the App Engine dependency.

The recommended way to create projects with App Engine enabled is via the [Project Factory module](https://github.com/terraform-google-modules/terraform-google-project-factory).
There is an example of how to create the project [within that module](https://github.com/terraform-google-modules/terraform-google-project-factory/tree/master/examples/app_engine)

### Configure a Service Account
In order to execute this module you must have a Service Account with the following roles.

- roles/storage.admin
- roles/pubsub.editor
- roles/cloudscheduler.admin
- roles/cloudfunctions.developer
- roles/iam.serviceAccountUser


### Enable API's
In order to operate with the Service Account you must activate the following API on the project where the Service Account was created:

- Cloud Scheduler API - cloudscheduler.googleapis.com
- Cloud PubSub API - pubsub.googleapis.com
- Cloud Functions API - cloudfunctions.googleapis.com

## Install

### Terraform
Be sure you have the correct Terraform version (0.12.x), you can choose the binary here:
- https://releases.hashicorp.com/terraform/
