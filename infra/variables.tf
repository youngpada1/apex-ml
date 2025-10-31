variable "github_token" {
  description = "GitHub Personal Access Token (with repo and workflow scopes)"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub username or org name"
  type        = string
  default     = "youngpada1"
}

variable "repository" {
  description = "Target GitHub repository name"
  type        = string
  default     = "apex-ml"
}

variable "branch" {
  description = "Target branch name"
  type        = string
  default     = "main"
}
