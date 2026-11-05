# Terraform — Hetzner Cloud (Production)

Создаёт production инфраструктуру в Hetzner Cloud (Европа).

## Что будет создано

**Phase 1 (MVP):**
- **Сервер api-1** — Ubuntu 22.04, CX22 (2 vCPU, 4 GB RAM, ~€4.5/мес)
- **SSH ключ** в Hetzner
- **Файрвол** — открыты порты 22, 80, 443

**Phase 2 (раскомментировать по мере роста):**
- Второй API сервер api-2
- Private Network 10.0.1.0/24
- Load Balancer LB11
- Staging сервер

## Предварительные требования

### 1. Создать аккаунт в Hetzner

[console.hetzner.com](https://console.hetzner.com) → создать проект `harvester`

### 2. Получить API токен

Hetzner Console → проект → Security → API Tokens → **Generate API Token** (Read & Write)

### 3. SSH ключ

```bash
# Если ключа нет — создать
ssh-keygen -t ed25519 -C "harvester-hetzner"

# Получить публичный ключ
cat ~/.ssh/id_ed25519.pub
```

## Шаг 1 — Настроить переменные

```bash
cd infra/terraform/hetzner
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # заполнить hcloud_token и ssh_public_key
```

## Шаг 2 — Настроить хранение state в GitLab

```bash
export TF_HTTP_ADDRESS="https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/terraform/state/hetzner"
export TF_HTTP_LOCK_ADDRESS="https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/terraform/state/hetzner/lock"
export TF_HTTP_UNLOCK_ADDRESS="https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/terraform/state/hetzner/lock"
export TF_HTTP_USERNAME="YOUR_GITLAB_USERNAME"
export TF_HTTP_PASSWORD="YOUR_GITLAB_PERSONAL_ACCESS_TOKEN"  # scope: api
```

`YOUR_PROJECT_ID`: GitLab → проект → Settings → General → Project ID.

## Шаг 3 — Инициализировать и запустить

```bash
terraform init    # скачивает hcloud провайдер
terraform plan    # проверить что будет создано
terraform apply   # создаёт сервер (~1 минута)
```

После `apply`:

```
Outputs:
api_1_ip    = "1.2.3.4"
ssh_command = "ssh deploy@1.2.3.4"
```

## Шаг 4 — Дождаться cloud-init

```bash
ssh deploy@<IP>  # через ~3 минуты после apply
sudo cloud-init status --wait
docker --version
```

## Шаг 5 — Подключить домен

В Cloudflare DNS добавить A-запись:
```
app.твой-домен.com → <IP сервера>
```

## Шаг 6 — Следующие шаги

1. Развернуть приложение → [docker/README.md](../../docker/README.md)
2. Настроить Caddy → [server/README.md](../../server/README.md)
3. Зарегистрировать GitLab Runner → см. ниже

## GitLab Runner

```bash
ssh deploy@<IP>

# GitLab → проект → Settings → CI/CD → Runners → New project runner
sudo gitlab-runner register \
  --url https://gitlab.com \
  --registration-token YOUR_TOKEN \
  --executor shell \
  --description "hetzner-production" \
  --tag-list "hetzner"
```

## Ограничить SSH своим IP (рекомендуется)

После первого подключения заменить в `firewall.tf`:

```hcl
# Было:
source_ips = ["0.0.0.0/0", "::/0"]

# Стало (свой IP — узнать: curl ifconfig.me):
source_ips = ["1.2.3.4/32"]
```

Затем: `terraform apply`

## Удалить всё

```bash
terraform destroy
```
