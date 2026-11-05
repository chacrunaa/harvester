# Harvester

Конвейер, который проводит продуктовую задачу через фазы — от бизнес-анализа
до тестирования. Каждую фазу ведёт агент-оркестратор, часть работы идёт
параллельно, между фазами стоят гейты. Агенты не вызывают друг друга: они
обмениваются файлами, а движок следит за изменениями и запускает следующего.

В репозитории **две версии одного продукта**: движок-сервис и переосмысление
той же идеи в виде CLI.

```
harvester/
├── engine/   v1 — Go-сервис: watcher на fsnotify, AND-гейты, REST + WebSocket,
│                  веб-интерфейс на React и TypeScript
├── cli/      v2 — CLI harv на Python без зависимостей: состояние задачи
│                  в файлах проекта, роли исполняют агенты в чатах
├── ui/       статичная витрина с проигрывателями настоящих прогонов
└── tools/    генераторы данных для витрины
```

**Начать проще всего с витрины** — она открывается двойным кликом, без сборки
и сервера:

```bash
open ui/index.html
```

---

## v1 — движок конвейера (`engine/`)

| Слой | Технологии |
|---|---|
| Движок | Go 1.22, `fsnotify` — модуль `harvester/scripts` |
| API | Go 1.22, Gin, `gorilla/websocket` — модуль `harvester/backend` |
| Состояние | атомарная запись JSON, без СУБД |
| Интерфейс | React 18, TypeScript 5.6, Vite 5, MUI 6, TanStack Query, Zustand |
| Инфраструктура | Docker, Terraform (Hetzner, Yandex), cloud-init, Caddy |

```
office-manager (init)
    ↓
[business]     product-manager → 4 аналитика параллельно → сведение
    ↓ OK / NOT OK
[systemic]     owner → analyst ↔ architect → spec
    ↓ OK / NOT OK
[development]  dev-lead → backend, frontend параллельно → reviewers
    ↓ OK / NOT OK
[testing]      qa-lead → qa, penetration параллельно
    ↓
office-manager (finish)
```

Порядок фаз и состав гейтов заданы в `.ai/scripts/pipeline-watcher.go`
(`phaseOrder`, `phaseOrchestrators`, `andGates`), состав 16 агентов —
в `templates/ai/pipeline-state.json`.

```bash
cd engine
cp infra/.env.example infra/.env     # выбрать провайдера, вписать один ключ
make install                         # go mod download + npm ci
make dev                             # API :3100, интерфейс :5173
```

## v2 — CLI `harv` (`cli/`)

Python 3.11+, **только стандартная библиотека**. 24 команды, 8 стадий,
4 группы ролей — по группе на чат агента.

Интересное здесь — не команды, а дисциплина:

- **Правило одного писателя.** Чат берёт только задачи своей стадии,
  поэтому четыре чата можно держать открытыми одновременно.
- **`advance`** — валидирующая передача: проверяет, что стадия оставила
  обязательные артефакты и что они зарегистрированы, иначе отказывает.
- **`--expect-revision`** — оптимистичная блокировка: если задачу успел
  изменить другой чат, команда откажет вместо того, чтобы затереть чужую работу.
- **`fanout`** — параллельные ветки группы dev с барьером на соединении.

```bash
cd cli/backend
make install && ln -sf "$PWD/dist/harv" ~/.local/bin/harv
harv init /path/to/project --personal
harv create "Описание задачи"
```

---

## Проверено

Всё ниже выполнено на macOS 15 (Apple Silicon) с Go 1.25, Node 22, Python 3.14,
Docker 28. Минимальные версии — Go 1.22, Node 20, Python 3.11.

| Команда | Результат |
|---|---|
| `cd engine/.ai/scripts && go test ./...` | 34 теста, зелёные |
| `cd engine/app/backend && go test ./...` | 4 теста, зелёные |
| `cd engine/app/frontend && npm ci && npm run build` | собирается, `tsc` без ошибок |
| `cd engine && make dev` | API `:3100`, интерфейс `:5173` |
| `curl localhost:3100/health` | `{"status":"ok"}` |
| `docker build -f infra/docker/Dockerfile -t harvester/api .` | образ ~35 МБ |
| контейнер + `curl /health` | отвечает |
| `cd cli/backend && make test` | 65 тестов, зелёные |
| `cd cli/backend && make check` | компиляция и smoke-test CLI |
| `open ui/index.html` | работает через `file://`, без сервера |

Данные для проигрывателей на витрине не нарисованы руками, а записаны
прогонами настоящего кода:

```bash
cd engine && make trace                          # поднимает реальный PipelineWatcher
python3 tools/trace-cli.py ui/data/cli-run.js    # реальный прогон harv
cd engine && make diagrams                       # схемы Canvas → SVG
```

Оба прогона работают **без ключей LLM**: это машины состояний над файлами.

---

## Чего здесь нет

Честный список, чтобы не тратить ваше время:

- **Десктоп-сборка на Tauri не собирается.** Оболочка написана, но sidecar
  ищется по пути от более ранней версии бэкенда на NestJS. Рабочий режим — веб.
- **`engine/templates/web|mobile|desktop` — спецификации, а не код:**
  30 markdown-файлов с описанием модулей. В новый проект копируется только
  `templates/ai/`.
- **Инфраструктура не развёрнута.** Terraform, cloud-init и Caddy описаны
  целиком, но на реальный сервер не выкатывались.
- **CI нет.** Образы собираются вручную.
- **Покрытие неравномерное:** движок конвейера покрыт содержательно, слои
  `service` и `repository` бэкенда — нет. У фронтенда только `tsc` и eslint.
- **Правая колонка веб-интерфейса — заглушки** (`StatusPanel`, `ReportsPanel`).
- **`fanout` не доводит ветки до конца без настроенного провайдера модели.**

## История

Обе версии писались как пет-проект с помощью ИИ-агентов — в том числе сам
Harvester применялся для работы над собой. Репозиторий собран из двух
отдельных репозиториев; история коммитов в него пока не перенесена.
