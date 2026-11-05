# Server — конфиги и скрипты на сервере

Файлы, которые живут непосредственно на сервере: Caddy (reverse proxy) и мониторинг диска.

## Файлы

| Файл | Куда копировать на сервере |
|---|---|
| `Caddyfile` | `/etc/caddy/Caddyfile` |
| `disk-monitor.sh` | `/opt/backup/disk-monitor.sh` (устанавливается через cloud-init) |

## Caddy — настройка HTTPS

Caddy получает SSL сертификат от Let's Encrypt автоматически.

### Установка конфига

```bash
scp infra/server/Caddyfile deploy@<IP>:/tmp/Caddyfile
ssh deploy@<IP>

# Заменить домен (по умолчанию стоит app.harvester.example.com)
sudo nano /tmp/Caddyfile

sudo mv /tmp/Caddyfile /etc/caddy/Caddyfile
sudo caddy validate --config /etc/caddy/Caddyfile
sudo caddy reload --config /etc/caddy/Caddyfile
```

### Что делает Caddyfile

- Принимает HTTPS запросы на домене
- Проксирует на `localhost:8080` (Go API в Docker)
- Автоматически получает и обновляет SSL сертификат
- Добавляет security headers (HSTS, X-Frame-Options и др.)
- Пишет JSON логи с ротацией

> **Важно**: для получения сертификата DNS уже должен указывать на IP сервера
> и порт 80 должен быть открыт (для ACME challenge).

## disk-monitor.sh — мониторинг диска

Скрипт проверяет заполненность диска каждые 30 минут.
Если больше 80% — шлёт алерт в Telegram.

Устанавливается автоматически через cloud-init.
Для активации нужно добавить Telegram credentials в `/opt/backup/.env`:

```bash
# Создать /opt/backup/.env на сервере:
ssh deploy@<IP>
cat > /opt/backup/.env << 'EOF'
TELEGRAM_BOT_TOKEN=123456:ABC-токен-бота
TELEGRAM_CHAT_ID=ваш-chat-id
EOF
chmod 600 /opt/backup/.env
```

**Получить Telegram credentials:**
1. Создать бота через [@BotFather](https://t.me/BotFather) → получить токен
2. Написать боту сообщение, открыть `https://api.telegram.org/bot<TOKEN>/getUpdates` → скопировать `chat.id`

Посмотреть лог мониторинга:
```bash
tail -f /var/log/harvester/disk-monitor.log
```

## Что самовосстанавливается само

| Ситуация | Кто лечит |
|---|---|
| Контейнер упал (crash, OOM) | Docker — `restart: unless-stopped` |
| VM перезагрузилась | systemd — `docker.service` и `caddy.service` в автозапуске |
| Приложение не отвечает на HTTP | Docker healthcheck — перезапускает контейнер |

## Uptime Robot — внешний мониторинг

1. Зарегистрироваться на [uptimerobot.com](https://uptimerobot.com) (бесплатно)
2. Добавить монитор: **HTTP(S)** → `https://твой-домен/health` → каждые **5 минут**
3. Установить **Alert after 3 failed checks** — исключает ложные алерты при перезапуске контейнера
4. Настроить алерт в Telegram: My Settings → Alert Contacts → Add → Telegram
