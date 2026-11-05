# ── Файрвол для API серверов ──────────────────────────────────────────────────

resource "hcloud_firewall" "api" {
  name = "harvester-api"

  # SSH — TODO: после первого входа заменить 0.0.0.0/0 на свой IP: ["1.2.3.4/32"]
  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "22"
    source_ips  = ["0.0.0.0/0", "::/0"]
    description = "SSH — ограничить своим IP"
  }

  # HTTP нужен для Let's Encrypt ACME challenge (Caddy)
  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "80"
    source_ips  = ["0.0.0.0/0", "::/0"]
    description = "HTTP / ACME"
  }

  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
    description = "HTTPS"
  }

  rule {
    direction        = "out"
    protocol         = "tcp"
    port             = "any"
    destination_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction        = "out"
    protocol         = "udp"
    port             = "any"
    destination_ips  = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction        = "out"
    protocol         = "icmp"
    destination_ips  = ["0.0.0.0/0", "::/0"]
  }
}
