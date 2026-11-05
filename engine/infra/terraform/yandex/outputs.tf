output "api_public_ip" {
  description = "Публичный IP VM — добавить в GitLab CI Variables (STAGING_IP)"
  value       = yandex_compute_instance.api.network_interface[0].nat_ip_address
}

output "ssh_command" {
  description = "SSH команда для подключения"
  value       = "ssh ubuntu@${yandex_compute_instance.api.network_interface[0].nat_ip_address}"
}
