#!/bin/bash
# Мониторинг диска — шлёт алерт в Telegram если заполненность > THRESHOLD%.
#
# Устанавливается автоматически через cloud-init в /opt/backup/disk-monitor.sh.
# Этот файл — справочная копия в репозитории.
#
# Для работы добавить в /opt/backup/.env на сервере:
#   TELEGRAM_BOT_TOKEN=<токен бота>
#   TELEGRAM_CHAT_ID=<ID чата>
#
# Cron (уже настроен через cloud-init):
#   */30 * * * * /opt/backup/disk-monitor.sh >> /var/log/harvester/disk-monitor.log 2>&1

set -euo pipefail

THRESHOLD=80
ENV_FILE="/opt/backup/.env"

[ -f "$ENV_FILE" ] && source "$ENV_FILE"

[ -z "${TELEGRAM_BOT_TOKEN:-}" ] && exit 0
[ -z "${TELEGRAM_CHAT_ID:-}" ] && exit 0

USAGE=$(df / | awk 'NR==2 {print $5+0}')
HOST=$(hostname)

if [ "$USAGE" -gt "$THRESHOLD" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=Диск заполнен на ${USAGE}% на ${HOST}. Нужна чистка." \
        > /dev/null
fi
