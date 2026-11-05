variable "hcloud_token" {
  description = "Hetzner Cloud API token (read & write)"
  type        = string
  sensitive   = true
}

variable "ssh_public_key" {
  description = "SSH public key content (cat ~/.ssh/id_ed25519.pub)"
  type        = string
}

variable "location" {
  description = "Hetzner datacenter location"
  type        = string
  default     = "hel1"  # Helsinki — минимальный пинг для СНГ
}

variable "server_type_api" {
  description = "Server type for API servers"
  type        = string
  default     = "cx22"  # Phase 1: cx22 (4GB). Phase 2: cpx21 (AMD, быстрее)
}

variable "server_type_staging" {
  description = "Server type for staging server (Phase 2)"
  type        = string
  default     = "cx11"  # 2GB, дешевле
}
