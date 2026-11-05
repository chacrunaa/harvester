terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.122"
    }
  }

  # Terraform state хранится в GitLab (бесплатно).
  # Настроить через env переменные перед запуском — см. terraform.tfvars.example.
  backend "http" {}
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.zone
}

# ── Сеть ─────────────────────────────────────────────────────────────────────

resource "yandex_vpc_network" "main" {
  name = "harvester-net"
}

resource "yandex_vpc_subnet" "main" {
  name           = "harvester-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = ["10.0.1.0/24"]
}

# ── Security Group (аналог файрвола) ──────────────────────────────────────────

resource "yandex_vpc_security_group" "api" {
  name       = "harvester-api"
  network_id = yandex_vpc_network.main.id

  # SSH — TODO: после первого входа заменить cidr на свой IP: ["1.2.3.4/32"]
  ingress {
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "SSH — ограничить своим IP"
  }

  # HTTP нужен для Let's Encrypt ACME challenge (Caddy)
  ingress {
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "HTTP / ACME"
  }

  ingress {
    protocol       = "TCP"
    port           = 443
    v4_cidr_blocks = ["0.0.0.0/0"]
    description    = "HTTPS"
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── VM: API сервер (тестовая среда) ──────────────────────────────────────────

resource "yandex_compute_instance" "api" {
  name        = "harvester-api"
  platform_id = var.platform_id
  zone        = var.zone

  resources {
    cores         = var.api_cores
    memory        = var.api_memory_gb
    core_fraction = var.api_core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = var.ubuntu_image_id  # Ubuntu 22.04 LTS — см. variables.tf
      size     = 20                   # GB
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.main.id
    nat                = true  # публичный IP
    security_group_ids = [yandex_vpc_security_group.api.id]
  }

  metadata = {
    user-data = file("${path.module}/../../cloud-init/setup-api.sh")
    ssh-keys  = "ubuntu:${var.ssh_public_key}"
  }

  scheduling_policy {
    preemptible = var.preemptible  # прерываемая VM дешевле ~3x, для тестов ок
  }
}
