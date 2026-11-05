# Terraform — Yandex Cloud (Staging / Тест)

Создаёт тестовый сервер в Yandex Cloud.
Используй для проверки деплоя до выхода на production в Hetzner.

## Что будет создано

- **VM** — Ubuntu 22.04, 2 vCPU, 4 GB RAM (или дешевле с `preemptible = true`)
- **VPC сеть** и подсеть `10.0.1.0/24`
- **Security Group** — открыты порты 22, 80, 443

После создания VM cloud-init автоматически установит Docker, Caddy и настроит пользователя `ubuntu`.

## Предварительные требования

### 1. Установить Yandex Cloud CLI

```bash
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
exec -l $SHELL
yc --version
```

### 2. Авторизоваться

```bash
yc init
```

### 3. Узнать Cloud ID и Folder ID

```bash
yc config list
# cloud-id: xxxxxxxxxxxxxxxx
# folder-id: xxxxxxxxxxxxxxxx
```

### 4. Получить OAuth токен

```bash
yc iam create-token
```

## Шаг 1 — Настроить переменные

```bash
cd infra/terraform/yandex
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # заполнить yc_token, yc_cloud_id, yc_folder_id, ssh_public_key
```

## Шаг 2 — Настроить хранение state в GitLab

```bash
export TF_HTTP_ADDRESS="https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/terraform/state/yandex"
export TF_HTTP_LOCK_ADDRESS="https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/terraform/state/yandex/lock"
export TF_HTTP_UNLOCK_ADDRESS="https://gitlab.com/api/v4/projects/YOUR_PROJECT_ID/terraform/state/yandex/lock"
export TF_HTTP_USERNAME="YOUR_GITLAB_USERNAME"
export TF_HTTP_PASSWORD="YOUR_GITLAB_PERSONAL_ACCESS_TOKEN"  # scope: api
```

> State Hetzner и Yandex хранятся под разными именами (`hetzner` vs `yandex`) — не перезаписывают друг друга.

## Шаг 3 — Инициализировать и запустить

```bash
terraform init
terraform plan
terraform apply
```

После `apply`:
```
Outputs:
api_public_ip = "123.45.67.89"
ssh_command   = "ssh ubuntu@123.45.67.89"
```

## Шаг 4 — Проверить что сервер готов

```bash
ssh ubuntu@<IP>  # через ~3 минуты
docker --version
sudo cat /var/log/cloud-init-output.log  # если что-то пошло не так
```

## Шаг 5 — Следующие шаги

1. Скопировать `.env` → [docker/README.md](../../docker/README.md)
2. Настроить Caddy → [server/README.md](../../server/README.md)
3. Зарегистрировать GitLab Runner → см. ниже

## GitLab Runner

```bash
ssh ubuntu@<IP>

sudo gitlab-runner register \
  --url https://gitlab.com \
  --registration-token YOUR_TOKEN \
  --executor shell \
  --description "yandex-staging" \
  --tag-list "hetzner"
```

## Сэкономить на тестах

```hcl
preemptible       = true   # VM останавливается через 24ч, но дешевле ~3x
api_core_fraction = 20     # burstable vCPU, дешевле при малой нагрузке
```

## Удалить всё

```bash
terraform destroy
```
