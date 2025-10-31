output "repository_url" {
  value = data.github_repository.repo.html_url
}

output "workflow_file_path" {
  value = github_repository_file.workflow_generate_readme.file
}

output "generator_script_path" {
  value = github_repository_file.generator_script.file
}
