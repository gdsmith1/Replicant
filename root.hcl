# Main Terragrunt configuration file
remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  config = {
    bucket         = "replicant-terraform-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "replicant-lock-table"
  }
}

inputs = {
  terragrunt_dir = get_terragrunt_dir()
}