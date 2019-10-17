module "bts_bigtable" {
  source			= "git::ssh://git@github.com/terraform-google-modules/terraform-google-scheduled-function.git"
  project_id			= var.project_id
  job_name			= "bts_bigtable"
  job_schedule			= var.job_schedule
  function_entry_point		= var.function_entry_point
  function_source_directory	= "bts"
  function_name			= "bts_bigtable"
  function_runtime		= var.function_runtime
  function_timeout_s		= "61"
  function_available_memory_mb	= "128"
  region			= var.region
  topic_name			= "bts_bigtable_scheduler"
  message_data			= base64encode(var.bts_bigtable_data)
}
