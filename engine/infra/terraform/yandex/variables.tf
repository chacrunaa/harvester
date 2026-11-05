variable "yc_token" {
  description = "Yandex Cloud OAuth token (yc iam create-token)"
  type        = string
  sensitive   = true
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID (yc config get cloud-id)"
  type        = string
}

variable "yc_folder_id" {
  description = "Yandex Cloud Folder ID (yc config get folder-id)"
  type        = string
}

variable "zone" {
  description = "Availability zone"
  type        = string
  default     = "ru-central1-a"
}

variable "ssh_public_key" {
  description = "SSH public key content (cat ~/.ssh/id_ed25519.pub)"
  type        = string
}

# ── VM параметры ──────────────────────────────────────────────────────────────

variable "platform_id" {
  description = "VM platform"
  type        = string
  default     = "standard-v3"  # Intel Ice Lake — оптимальный по цене/производительности
}

variable "api_cores" {
  description = "vCPU count"
  type        = number
  default     = 2
}

variable "api_memory_gb" {
  description = "RAM in GB"
  type        = number
  default     = 4
}

variable "api_core_fraction" {
  description = "Guaranteed vCPU fraction (100 = dedicated, 20/50 = burstable, дешевле)"
  type        = number
  default     = 20  # для тестов достаточно, ~в 3x дешевле
}

variable "preemptible" {
  description = "Прерываемая VM — значительно дешевле, останавливается через 24ч. Для тестов ок."
  type        = bool
  default     = false
}

# ── Образ Ubuntu 22.04 ────────────────────────────────────────────────────────
# Получить актуальный ID:
#   yc compute image list --folder-id standard-images | grep ubuntu-22
variable "ubuntu_image_id" {
  description = "Ubuntu 22.04 LTS image ID в Yandex Cloud"
  type        = string
  default     = "fd8clogg1kull9084s9o"  # Ubuntu 22.04 — проверить актуальность!
}
