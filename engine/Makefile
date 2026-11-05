GO := go

.PHONY: help install dev run build go-build test test-go test-web lint trace diagrams env-encrypt env-decrypt clean

help:
	@echo "Harvester v1 — движок конвейера (Go) + веб-интерфейс (React/TS)"
	@echo
	@echo "  make install     зависимости: go mod download + npm ci"
	@echo "  make dev         бэкенд :3100 и Vite :5173 одновременно"
	@echo "  make run         только Go-бэкенд на :3100"
	@echo "  make build       бинарь dist/harvester-backend + бандл фронта"
	@echo "  make test        все тесты (Go + typecheck фронта)"
	@echo "  make trace       записать прогон движка для витрины ui/"
	@echo "  make diagrams    пересобрать схемы Canvas → SVG"
	@echo "  make clean       удалить артефакты сборки"
	@echo
	@echo "Требуется: Go 1.22+, Node 20+."

# ── Установка ──────────────────────────────────────────────────────
# .ai/scripts — это Go-модуль (harvester/scripts), не npm-пакет:
# он подключается к бэкенду через replace в app/backend/go.mod.
install:
	$(GO) work sync
	cd app/backend  && $(GO) mod download
	cd .ai/scripts  && $(GO) mod download
	cd app/frontend && npm ci

# ── Dev: Go-бэкенд + Vite одновременно ────────────────────────────
# Два процесса: API на :3100, интерфейс на :5173 (Vite проксирует
# /api и /ws на :3100, см. app/frontend/vite.config.ts).
dev:
	@trap 'kill 0' EXIT INT TERM; \
	cd app/backend && $(GO) run ./cmd/server & \
	cd app/frontend && npm run dev & \
	wait

# ── Dev: только бэкенд ────────────────────────────────────────────
run:
	cd app/backend && $(GO) run ./cmd/server

# ── Сборка Go-бэкенда ─────────────────────────────────────────────
go-build:
	cd app/backend && $(GO) build -o ../../dist/harvester-backend ./cmd/server

# ── Prod: бинарь + Vite-бандл ─────────────────────────────────────
build:
	$(MAKE) go-build
	cd app/frontend && npm run build

# ── Тесты ─────────────────────────────────────────────────────────
# Корень репозитория не является Go-модулем, поэтому go test ./...
# запускается внутри каждого модуля отдельно.
test: test-go test-web

test-go:
	cd .ai/scripts && $(GO) test ./...
	cd app/backend && $(GO) test ./...

test-web:
	cd app/frontend && npm run typecheck

lint:
	cd app/frontend && npm run lint

# ── Материалы для витрины ─────────────────────────────────────────
# Гоняет настоящий watcher на временном каталоге и пишет журнал
# переходов в ui/data/. Вызовов LLM не делает, ключи не нужны.
trace:
	cd .ai/scripts && $(GO) run ./cmd/pipeline-trace -out ../../../ui/data/engine-run.js

# Схемы архитектуры: Obsidian Canvas → SVG, который открывается
# в любом браузере.
diagrams:
	python3 ../tools/canvas-to-svg.py assets/canvas/chat-engine.canvas \
		-o ../ui/img/chat-engine.svg --title "Цикл одного хода агента"
	python3 ../tools/canvas-to-svg.py assets/canvas/agent-interaction.canvas \
		-o ../ui/img/agent-interaction.svg --title "Взаимодействие агентов и гейты"

# ── Секреты (GPG) ─────────────────────────────────────────────────
# Шифруют infra/.env в infra/environments и обратно. Зашифрованный
# файл в репозиторий не коммитится, пароль нигде не записан.
env-encrypt:
	@bash -c 'IFS= read -rsp "GPG passphrase: " pass || exit 1; echo; IFS= read -rsp "Repeat: " confirm || exit 1; echo; [ "$$pass" = "$$confirm" ] || { echo "Mismatch" >&2; exit 1; }; printf "%s" "$$pass" | gpg --batch --yes --pinentry-mode loopback --no-symkey-cache --passphrase-fd 0 --symmetric --armor -o infra/environments infra/.env'

env-decrypt:
	@bash -c '[ -f infra/environments ] || { echo "infra/environments отсутствует — шифровать нечего" >&2; exit 1; }; IFS= read -rsp "GPG passphrase: " pass || exit 1; echo; printf "%s" "$$pass" | gpg --batch --yes --pinentry-mode loopback --no-symkey-cache --passphrase-fd 0 --decrypt -o infra/.env infra/environments'

# ── Очистка ───────────────────────────────────────────────────────
clean:
	rm -rf app/frontend/dist app/frontend/src-tauri/target
	rm -rf app/frontend/node_modules
	rm -rf dist/
