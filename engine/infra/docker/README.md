# Docker — сборка и запуск приложения

Go API упакован в один образ и запускается через Docker Compose.

## Файлы

| Файл | Для чего |
|---|---|
| `Dockerfile` | Сборка Go API (multi-stage: `golang:1.22-alpine` → `alpine:3.19`) |
| `docker-compose.local.yml` | Локальная проверка образа |
| `docker-compose.prod.yml` | Запуск на сервере за Caddy |

## Про образ

Бэкенд состоит из **двух Go-модулей**: `app/backend` (сервер) и `.ai/scripts`
(движок конвейера), второй подключён первым через `replace` в `go.mod`.
Поэтому контекст сборки — корень `engine/`, и в образ копируются оба модуля.
Плюс промпты агентов, правила и скелет нового проекта (`.ai/agents`,
`.ai/skills`, `.ai/rules`, `templates/`) — они читаются с диска в рантайме.

Watcher состояния — это Go-библиотека внутри процесса API
(`app/backend/internal/service/watcher.go` поднимает `scripts.NewWatcher`),
а не отдельный контейнер.

Порт — `3100` (`app/backend/internal/constants/env.go`), переопределяется
переменной `PORT`. Liveness-проба — `GET /health`.

## Локальная проверка

```bash
cd engine
cp infra/.env.example infra/.env        # заполнить LLM_PROVIDER и ключ
docker compose -f infra/docker/docker-compose.local.yml up --build

curl http://localhost:3100/health       # {"status":"ok"}
```

## Запуск на сервере

CI в репозитории нет — образ собирается и публикуется вручную:

```bash
docker build -f infra/docker/Dockerfile -t <registry>/harvester/api:latest .
docker push <registry>/harvester/api:latest
```

Дальше на сервере:

```bash
ssh deploy@<IP>
cd /opt/harvester

cat > .env << 'EOF'
APP_ENV=production
PORT=3100
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-key
EOF
chmod 600 .env

HARVESTER_IMAGE=<registry>/harvester/api:latest docker compose up -d
docker compose logs -f
```

Проверить:

```bash
docker compose ps
curl http://localhost:3100/health
```

Наружу трафик отдаёт Caddy (`infra/server/Caddyfile`), порт слушается
только на `127.0.0.1`.

## Локальная разработка — без Docker

```bash
cd engine
make dev        # API :3100 и Vite :5173 одновременно
```
