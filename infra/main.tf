terraform {
  required_version = ">= 1.6.0"
  backend "local" {
    # This will use workspace-specific state files
    # Path will be: terraform.tfstate.d/<workspace>/terraform.tfstate
  }

  required_providers {
    github = {
      source  = "integrations/github"
      version = ">= 6.0.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

data "github_repository" "repo" {
  name = var.repository
}

# Trigger README generation workflow on apply
resource "null_resource" "trigger_readme_workflow" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      gh workflow run generate-readme.yml \
        --repo ${var.github_owner}/${var.repository} \
        || echo "Workflow trigger failed - ensure gh CLI is authenticated"
    EOT
  }
}