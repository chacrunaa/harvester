output "api_1_ip" {
  description = "Public IP api-1 — добавить в Cloudflare DNS и GitLab CI Variables (PROD_API_1_IP)"
  value       = hcloud_server.api_1.ipv4_address
}

output "ssh_command" {
  description = "SSH команда для подключения к серверу"
  value       = "ssh deploy@${hcloud_server.api_1.ipv4_address}"
}

# Phase 2 outputs — раскомментировать вместе с ресурсами в main.tf

# output "api_2_ip" {
#   value       = hcloud_server.api_2.ipv4_address
#   description = "Public IP api-2 — добавить в GitLab CI Variables (PROD_API_2_IP)"
# }
#
# output "staging_ip" {
#   value       = hcloud_server.staging.ipv4_address
#   description = "Public IP staging — добавить в GitLab CI Variables (STAGING_IP)"
# }
#
# output "load_balancer_ip" {
#   value       = hcloud_load_balancer.main.ipv4
#   description = "IP Load Balancer — заменить api_1_ip в Cloudflare DNS на этот"
# }
