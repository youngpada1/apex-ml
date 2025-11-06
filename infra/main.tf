terraform {
  required_version = ">= 1.6.0"
  backend "local" {
    # This will use workspace-specific state files
    # Path will be: terraform.tfstate.d/<workspace>/terraform.tfstate
  }
}