#!/bin/bash
# Cloud-init script для API серверов (api-1, api-2, staging)
# Выполняется ОДИН РАЗ автоматически при создании сервера через Terraform.
# Время выполнения: ~3-5 минут.
set -euo pipefail

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a /var/log/cloud-init-custom.log; }

log "=== Harvester API server setup started ==="

# ── Обновление ────────────────────────────────────────────────────────────────
apt-get update -y
apt-get upgrade -y
apt-get install -y curl wget git htop vim jq ca-certificates gnupg lsb-release

log "Base packages installed"

# ── Docker ───────────────────────────────────────────────────────────────────
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

systemctl enable docker
systemctl start docker
log "Docker installed"

# ── Пользователь deploy ───────────────────────────────────────────────────────
useradd -m -s /bin/bash deploy
usermod -aG docker deploy

mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
log "User 'deploy' created"

# ── Директории ───────────────────────────────────────────────────────────────
mkdir -p /opt/harvester && chown deploy:deploy /opt/harvester
mkdir -p /opt/harvester-staging && chown deploy:deploy /opt/harvester-staging
mkdir -p /opt/backup && chown deploy:deploy /opt/backup
mkdir -p /var/log/harvester && chown deploy:deploy /var/log/harvester

# ── Caddy (reverse proxy + SSL) ───────────────────────────────────────────────
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y && apt-get install -y caddy
systemctl enable caddy
log "Caddy installed"

# ── GitLab Runner (только api-1, ручная регистрация после) ───────────────────
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | bash
apt-get install -y gitlab-runner
usermod -aG docker gitlab-runner
log "GitLab Runner installed — requires manual registration (see runbook Day 4)"

# ── Мониторинг диска ─────────────────────────────────────────────────────────
# Скрипт шлёт алерт в Telegram если диск заполнен > 80%.
# Telegram credentials берёт из /opt/backup/.env.
cat > /opt/backup/disk-monitor.sh << 'SCRIPT'
#!/bin/bash
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
SCRIPT

chmod +x /opt/backup/disk-monitor.sh
chown deploy:deploy /opt/backup/disk-monitor.sh

# Запускать каждые 30 минут от пользователя deploy
(crontab -u deploy -l 2>/dev/null; echo "*/30 * * * * /opt/backup/disk-monitor.sh >> /var/log/harvester/disk-monitor.log 2>&1") \
    | crontab -u deploy -

log "Disk monitor installed (cron every 30 min)"

# ── Безопасность ─────────────────────────────────────────────────────────────
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

log "=== Setup complete: $(date) ==="
