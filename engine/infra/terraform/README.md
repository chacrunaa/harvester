# Terraform — управление серверами

Terraform создаёт серверы в облаке по описанию в коде.
Вместо кликов в веб-интерфейсе описываешь что нужно в `.tf` файлах
и запускаешь `terraform apply`. Окружение воспроизводится с нуля за одну команду.

## Два провайдера — два окружения

```
terraform/
├── yandex/     # Staging / тестирование
└── hetzner/    # Production (Европа)
```

| | Yandex Cloud | Hetzner Cloud |
|---|---|---|
| **Цель** | Тест, staging | Production |
| **Расположение** | Россия | Европа (Helsinki) |
| **Стоимость** | ~₽800–1500/мес | ~€5–9/мес |
| **Когда использовать** | Быстрая проверка | Реальные пользователи |

## Установка Terraform

```bash
# Ubuntu / Debian
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# macOS
brew tap hashicorp/tap && brew install hashicorp/tap/terraform

terraform version  # >= 1.6
```

## Куда идти дальше

- [yandex/README.md](yandex/README.md) — поднять тестовый сервер в Yandex Cloud
- [hetzner/README.md](hetzner/README.md) — поднять production сервер в Hetzner

## Хранение state

Terraform state хранится в GitLab (бесплатно).
Настройка через переменные окружения — описано в README каждого провайдера.

> **Важно**: `terraform.tfvars` содержит API токены и находится в `.gitignore`.
> Никогда не коммить его в репозиторий.
