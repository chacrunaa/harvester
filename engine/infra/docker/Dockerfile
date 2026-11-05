# Go API — multi-stage build
#
# Бэкенд состоит из двух Go-модулей:
#   app/backend   — HTTP/WebSocket сервер (module harvester/backend)
#   .ai/scripts   — движок конвейера (module harvester/scripts)
# Второй подключается первым через replace в app/backend/go.mod,
# поэтому в образ нужно копировать оба, иначе go build не найдёт
# harvester/scripts.
#
# Сборка из корня engine/:
#   docker build -f infra/docker/Dockerfile -t harvester/api .

FROM golang:1.22-alpine AS builder
WORKDIR /build

# Зависимости — отдельный слой для кэша сборки.
COPY app/backend/go.mod app/backend/go.sum ./app/backend/
COPY .ai/scripts/go.mod .ai/scripts/go.sum ./.ai/scripts/
RUN cd app/backend && go mod download

COPY app/backend/ ./app/backend/
COPY .ai/scripts/ ./.ai/scripts/

RUN cd app/backend && CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-w -s" \
    -o /server \
    ./cmd/server

# ── Финальный образ ───────────────────────────────────────────────────────────
FROM alpine:3.19
RUN apk --no-cache add ca-certificates tzdata wget

WORKDIR /app
RUN adduser -D -u 1001 app

COPY --from=builder /server .

# Движку нужны промпты агентов, правила и скелет нового проекта:
# они читаются с диска во время работы, а не вшиты в бинарь.
COPY --chown=app:app .ai/agents/   ./.ai/agents/
COPY --chown=app:app .ai/skills/   ./.ai/skills/
COPY --chown=app:app .ai/rules/    ./.ai/rules/
COPY --chown=app:app templates/    ./templates/

USER app

# Порт по умолчанию из internal/constants/env.go, переопределяется PORT.
ENV PORT=3100
EXPOSE 3100

HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=15s \
  CMD wget -qO- http://localhost:3100/health || exit 1

ENTRYPOINT ["./server"]
