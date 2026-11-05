# app/

Клиент-серверное веб-приложение: Go-бэкенд и React-фронтенд.

```
app/
├── backend/      # Go 1.22 + Gin + gorilla/websocket, HTTP API на :3100
└── frontend/     # React 18 + TypeScript + Vite + MUI, dev-сервер на :5173
    └── src-tauri/    # Tauri 2 (Rust) — десктоп-оболочка, не достроена
```

Бэкенд — обычный HTTP/WebSocket сервер. Фронтенд в dev-режиме работает на
отдельном порту и проксирует `/api` и `/ws` на бэкенд
(`frontend/vite.config.ts`); статику бэкенд не раздаёт.

**Команды ниже — из каталога `engine/`.**

## Требования

- Go 1.22+
- Node.js 20+

## Установка и запуск

```bash
cp infra/.env.example infra/.env   # выбрать провайдера и вписать один ключ
make install                       # go mod download + npm ci
make dev                           # бэкенд :3100 + фронтенд :5173
```

Отдельно:

```bash
make run                                 # только Go-бэкенд
(cd app/frontend && npm run dev)         # только фронтенд, http://127.0.0.1:5173
```

## Когда пересобирать

| Изменил | Нужно |
|---------|-------|
| `backend/**` (Go) | перезапустить `make run` или `make dev` |
| `frontend/src/**` (React/TS) | ничего — Vite подхватит через HMR |
| `frontend/src-tauri/**` (Rust) | пересобрать Tauri — но см. ниже |

## Сборка

```bash
make build      # dist/harvester-backend + бандл фронтенда в app/frontend/dist
```

## Проверки

```bash
make test                                      # Go-тесты + typecheck фронта
(cd app/frontend && npm run typecheck && npm run lint)
(cd app/backend  && go vet ./...)
```

## Секреты

```bash
make env-encrypt    # infra/.env → infra/environments (GPG, пароль спрашивается)
make env-decrypt    # обратно
```

Зашифрованный файл в репозиторий не коммитится, пароль нигде не записан.
Переменные окружения бэкенда перечислены в `backend/.env.example`.

## Про Tauri

Десктоп-оболочка в `frontend/src-tauri/` написана (Rust, rusqlite для
настроек, JSON-RPC к дочернему процессу), но **не собирается**:
`src-tauri/src/lib.rs` ожидает sidecar по пути `backend/dist/main.js` и
запускает его через `node` — это осталось от более ранней версии бэкенда
на NestJS. Текущий Go-бэкенд говорит по HTTP, а не по stdio JSON-RPC, и
каталога `src-tauri/bin/` не существует. Рабочий режим — веб.
