terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.47"
    }
  }

  # Terraform state хранится в GitLab (бесплатно).
  # Настроить через env переменные перед запуском — см. terraform.tfvars.example.
  backend "http" {}
}

provider "hcloud" {
  token = var.hcloud_token
}

# ── SSH Key ───────────────────────────────────────────────────────────────────

resource "hcloud_ssh_key" "default" {
  name       = "harvester-key"
  public_key = var.ssh_public_key
}

# ── Phase 1: один API сервер ──────────────────────────────────────────────────
#
# Для MVP достаточно только этого блока.
# Phase 2 ресурсы закомментированы ниже.

resource "hcloud_server" "api_1" {
  name        = "api-1"
  image       = "ubuntu-22.04"
  server_type = var.server_type_api
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.default.id]
  user_data   = file("${path.module}/../../cloud-init/setup-api.sh")

  labels = {
    role = "api"
    env  = "production"
  }
}

resource "hcloud_firewall_attachment" "api_1" {
  firewall_id = hcloud_firewall.api.id
  server_ids  = [hcloud_server.api_1.id]
}

# ─────────────────────────────────────────────────────────────────────────────
# Phase 2 ресурсы — раскомментировать по мере роста
# ─────────────────────────────────────────────────────────────────────────────

# ── Private Network ───────────────────────────────────────────────────────────

# resource "hcloud_network" "private" {
#   name     = "harvester-net"
#   ip_range = "10.0.1.0/24"
# }
#
# resource "hcloud_network_subnet" "private" {
#   network_id   = hcloud_network.private.id
#   type         = "cloud"
#   network_zone = "eu-central"
#   ip_range     = "10.0.1.0/24"
# }
#
# resource "hcloud_server_network" "api_1" {
#   server_id  = hcloud_server.api_1.id
#   network_id = hcloud_network.private.id
#   ip         = "10.0.1.2"
# }

# ── API сервер 2 ──────────────────────────────────────────────────────────────

# resource "hcloud_server" "api_2" {
#   name        = "api-2"
#   image       = "ubuntu-22.04"
#   server_type = var.server_type_api
#   location    = var.location
#   ssh_keys    = [hcloud_ssh_key.default.id]
#   user_data   = file("${path.module}/../../cloud-init/setup-api.sh")
#   labels      = { role = "api", env = "production" }
# }
#
# resource "hcloud_server_network" "api_2" {
#   server_id  = hcloud_server.api_2.id
#   network_id = hcloud_network.private.id
#   ip         = "10.0.1.3"
# }
#
# resource "hcloud_firewall_attachment" "api_2" {
#   firewall_id = hcloud_firewall.api.id
#   server_ids  = [hcloud_server.api_2.id]
# }

# ── Staging сервер ────────────────────────────────────────────────────────────

# resource "hcloud_server" "staging" {
#   name        = "staging"
#   image       = "ubuntu-22.04"
#   server_type = var.server_type_staging
#   location    = var.location
#   ssh_keys    = [hcloud_ssh_key.default.id]
#   user_data   = file("${path.module}/../../cloud-init/setup-api.sh")
#   labels      = { role = "api", env = "staging" }
# }

# ── Load Balancer ─────────────────────────────────────────────────────────────

# resource "hcloud_load_balancer" "main" {
#   name               = "harvester-lb"
#   load_balancer_type = "lb11"
#   location           = var.location
#   labels             = { env = "production" }
# }
#
# resource "hcloud_load_balancer_network" "main" {
#   load_balancer_id = hcloud_load_balancer.main.id
#   network_id       = hcloud_network.private.id
#   ip               = "10.0.1.10"
# }
#
# resource "hcloud_load_balancer_service" "http" {
#   load_balancer_id = hcloud_load_balancer.main.id
#   protocol         = "http"
#   listen_port      = 80
#   destination_port = 8080
#   health_check {
#     protocol = "http"
#     port     = 8080
#     interval = 10
#     timeout  = 5
#     retries  = 3
#     http {
#       path         = "/health"
#       status_codes = ["200"]
#     }
#   }
# }
#
# resource "hcloud_load_balancer_service" "https" {
#   load_balancer_id = hcloud_load_balancer.main.id
#   protocol         = "https"
#   listen_port      = 443
#   destination_port = 8080
#   http {
#     certificates = []
#   }
#   health_check {
#     protocol = "http"
#     port     = 8080
#     interval = 10
#     timeout  = 5
#     retries  = 3
#     http {
#       path         = "/health"
#       status_codes = ["200"]
#     }
#   }
# }
#
# resource "hcloud_load_balancer_target" "api_1" {
#   load_balancer_id = hcloud_load_balancer.main.id
#   type             = "server"
#   server_id        = hcloud_server.api_1.id
#   use_private_ip   = true
# }
#
# resource "hcloud_load_balancer_target" "api_2" {
#   load_balancer_id = hcloud_load_balancer.main.id
#   type             = "server"
#   server_id        = hcloud_server.api_2.id
#   use_private_ip   = true
# }
