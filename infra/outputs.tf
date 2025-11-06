output "repository_url" {
  value       = data.github_repository.repo.html_url
  description = "GitHub repository URL"
}

output "environment" {
  value       = var.environment
  description = "Current Terraform workspace environment"
}

output "workflow_trigger" {
  value       = "README generation workflow triggered via GitHub Actions API"
  description = "Workflow automation status"
}
