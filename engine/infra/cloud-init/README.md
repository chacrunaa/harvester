# Cloud-init — автонастройка сервера

Cloud-init запускается один раз при первом старте VM.
Terraform передаёт скрипт как `user_data` — сервер настраивается без SSH.

## Файлы

| Файл | Для чего |
|---|---|
| `setup-api.sh` | API сервер (оба окружения: Yandex и Hetzner) |

## Что делает setup-api.sh

1. Обновляет пакеты системы
2. Устанавливает Docker и Docker Compose plugin
3. Создаёт пользователя `deploy` с доступом к Docker
4. Создаёт директории `/opt/harvester`, `/opt/backup`, `/var/log/harvester`
5. Устанавливает Caddy (reverse proxy с автоматическим SSL)
6. Устанавливает GitLab Runner (нужна ручная регистрация после — см. terraform README)
7. Устанавливает disk-monitor.sh в cron (каждые 30 минут)
8. Отключает root SSH вход

## Если сервер уже существует

Cloud-init не запустится повторно. Выполнить скрипт вручную:

```bash
scp infra/cloud-init/setup-api.sh ubuntu@<IP>:/tmp/
ssh ubuntu@<IP>
sudo bash /tmp/setup-api.sh
```

## Посмотреть лог выполнения

```bash
ssh ubuntu@<IP>
sudo cat /var/log/cloud-init-output.log
```

Время выполнения: ~3–5 минут.

→ Следующий шаг: [docker/README.md](../docker/README.md)
