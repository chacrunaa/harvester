# Harvester v1 — движок многоагентного конвейера

Система проводит продуктовую задачу через четыре фазы — от бизнес-анализа
до тестирования. Каждую фазу ведёт агент-оркестратор, внутри фазы часть
агентов работает параллельно, между фазами стоит ручной гейт OK / NOT OK.

Обмен между агентами идёт **через файлы**: агент пишет результат в свой
каталог, Go-watcher видит изменение через `fsnotify`, по карте маршрутов
копирует файл во входной каталог следующего агента и запускает его.

## Стек

| Слой | Технология |
|---|---|
| Движок конвейера | Go 1.22, `fsnotify` — модуль `harvester/scripts` в `.ai/scripts` |
| HTTP / WebSocket API | Go 1.22, Gin, `gorilla/websocket` — модуль `harvester/backend` |
| Хранение состояния | атомарная запись JSON на диск, без СУБД |
| Веб-интерфейс | React 18, TypeScript 5.6, Vite 5, MUI 6, TanStack Query, Zustand |
| Десктоп-оболочка | Tauri 2 (Rust, rusqlite) — не достроена, см. «Ограничения» |
| LLM-провайдеры | Claude, OpenAI, DeepSeek, Gemini — выбирается один |

Два Go-модуля связаны через `replace` в `app/backend/go.mod`, оба
перечислены в `go.work`.

## Структура

```
engine/
  .ai/
    agents/        17 промптов ролей + 16 карт маршрутов (*.route-map.json)
    skills/        15 навыков, подгружаются в промпт по ссылке
    rules/         правила архитектуры, Go, фронтенда и документации
    scripts/       Go-модуль: watcher, запуск агента, клиент LLM, парсер ответов
  app/
    backend/       Go: Gin + WebSocket, слои config/domain/repository/service/transport
    frontend/      React + Vite + MUI, Tauri-оболочка в src-tauri/
  templates/
    ai/            скелет .ai/ для нового проекта (состояние + каталоги чатов)
    web|mobile|desktop/   спецификации типовых приложений (markdown, без кода)
  infra/           Terraform, cloud-init, Docker, Caddy
  assets/canvas/   исходники схем архитектуры (Obsidian Canvas)
```

## Конвейер

Порядок фаз задан в `.ai/scripts/pipeline-watcher.go` (`phaseOrder`):

```
office-manager (init)
    ↓
[business]     product-manager → product-analyst, market-analyst,
                                 strategist, financier (параллельно)
                               → product-manager сводит результаты
    ↓ OK / NOT OK
[systemic]     owner → analyst → (вопросы ↔ ответы с architect) → spec → owner
    ↓ OK / NOT OK
[development]  dev-lead → backend, frontend (параллельно) → reviewers
    ↓ OK / NOT OK
[testing]      qa-lead → qa, penetration (параллельно)
    ↓ OK / NOT OK
office-manager (finish)
```

**AND-гейт.** Для фаз `business` и `development` в коде объявлен
`andGates`: следующий шаг запускается только когда *все* параллельные
агенты фазы в статусе `done`. Фаза переключается, когда оркестратор
фазы завершил работу.

16 агентов участвуют в конвейере и перечислены в
`templates/ai/pipeline-state.json`. Семнадцатый, `figma-designer`, имеет
промпт и навык, но не имеет карты маршрутов и в состоянии конвейера не
числится — он вне конвейера.

## Требования

Go 1.22+, Node 20+. Для десктоп-сборки дополнительно Rust — но она не
работает, см. «Ограничения».

## Запуск

```bash
cp infra/.env.example infra/.env     # выбрать провайдера, вписать один ключ
make install                         # go mod download + npm ci
make dev                             # API :3100 и интерфейс :5173
```

Это **два процесса**: Go-сервер на `:3100` и Vite на `:5173`. Vite
проксирует `/api` и `/ws` на бэкенд (`app/frontend/vite.config.ts`),
статику Go-сервер не раздаёт.

| Команда | Что делает |
|---|---|
| `make install` | `go work sync`, `go mod download` в двух модулях, `npm ci` |
| `make dev` | бэкенд и фронтенд одновременно |
| `make run` | только Go-бэкенд на `:3100` |
| `make build` | бинарь `dist/harvester-backend` + бандл фронтенда |
| `make test` | Go-тесты обоих модулей + `tsc` фронтенда |
| `make trace` | записать прогон движка для витрины `ui/` |
| `make diagrams` | пересобрать схемы Canvas → SVG |

Настройки провайдера читаются из `app/backend/.env` или `infra/.env`
(см. `app/backend/.env.example` — там полный список переменных).
Проверка живости: `curl localhost:3100/health`.

## Тесты

```bash
make test-go     # 38 тестов
```

- `.ai/scripts` — 34 теста: переходы фаз, AND-гейт, построение контекста
  агента, парсинг ответа LLM, атомарная запись файлов.
- `app/backend` — 4 теста: карта маршрутов, `/health`, CORS и preflight.

Покрытие неравномерное: движок конвейера покрыт содержательно, у слоёв
`service` и `repository` бэкенда тестов нет.

## Docker

```bash
docker build -f infra/docker/Dockerfile -t harvester/api .
docker compose -f infra/docker/docker-compose.local.yml up --build
```

Образ ~35 МБ, один сервис. Watcher конвейера — библиотека внутри
процесса API, а не отдельный контейнер.

## Ограничения

Честно о том, что не работает:

- **Tauri-сборка не собирается.** `src-tauri/src/lib.rs` ищет sidecar по
  пути `app/backend/dist/main.js` и запускает его через `node` — это
  наследие более ранней версии на NestJS. Go-бэкенд говорит по HTTP, а не
  по stdio JSON-RPC, и `src-tauri/bin/` не существует. Рабочий режим —
  веб (`make dev`).
- **`templates/web|mobile|desktop` — это спецификации, а не код.** 30
  markdown-файлов с описанием модулей и ожидаемой структуры. Копируется в
  новый проект только `templates/ai/`.
- **Инфраструктура не развёрнута.** Terraform, cloud-init и Caddy описаны
  целиком, но на реальный сервер не выкатывались. CI в репозитории нет.
- **`.ai/scripts/inits/init.go`** никем не вызывается: ту же логику
  копирования скелета реализует `app/backend/internal/transport/http/projects.go`.

## Куда смотреть дальше

| Файл | О чём |
|---|---|
| `.ai/README.md` | устройство движка: агенты, навыки, карты маршрутов, протокол файлов |
| `.ai/agents/` | промпты ролей и карты маршрутов — поведение каждого агента |
| `app/backend/.env.example` | полный список переменных окружения |
| `infra/README.md` | инфраструктура и порядок развёртывания |
| `../ui/engine.html` | схемы архитектуры и проигрыватель прогона |
