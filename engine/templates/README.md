# templates

Два разных по природе набора: рабочий скелет состояния и справочные
спецификации типовых приложений.

## Структура

```
templates/
├── ai/        — скелет .ai/ для нового проекта: pipeline-state.json,
│                каталоги чатов всех 16 агентов, backlog, history
├── web/       — спецификации веб-приложений (10 типов)
├── mobile/    — спецификации мобильных приложений (11 типов)
└── desktop/   — спецификации десктопных приложений (9 типов)
```

## Как используется

`ai/` копируется в рабочий каталог нового проекта как `.ai/` — это
делает обработчик `POST /api/projects/create`
(`app/backend/internal/transport/http/projects.go`), заполняя `task_id` и
`created_at` в `pipeline-state.json`.

**Платформенные каталоги кода не содержат.** Каждый из 30 типов — это
один `README.md` с описанием ключевых модулей, предполагаемого стека и
ожидаемой структуры файлов. Это материал для агентов на этапе
проектирования, а не исполняемый бойлерплейт: автоматически они никуда не
копируются.

Отметим и расхождение: спецификации предлагают Next.js + NestJS +
PostgreSQL + Redis, тогда как сам Harvester собран на Go + React/Vite и
хранит состояние в JSON-файлах.

## Web — типы приложений

| Тип | Описание |
|-----|----------|
| [messenger](./web/messenger/) | Чат, коммуникационная платформа |
| [crm](./web/crm/) | CRM, управление клиентами и воронкой |
| [e-commerce](./web/e-commerce/) | Интернет-магазин, каталог, оплата |
| [dashboard](./web/dashboard/) | Аналитический дашборд, метрики |
| [saas](./web/saas/) | SaaS с подпиской, мультитенантностью |
| [marketplace](./web/marketplace/) | Маркетплейс, p2p-торговля |
| [task-manager](./web/task-manager/) | Таск-менеджер, канбан |
| [landing](./web/landing/) | Лендинг, маркетинговый сайт |
| [ai-tool](./web/ai-tool/) | AI-инструмент, LLM-чат, RAG |
| [social](./web/social/) | Соцсеть, community, лента |

## Mobile — типы приложений

| Тип | Описание |
|-----|----------|
| [messenger](./mobile/messenger/) | Мессенджер, чат, звонки |
| [e-commerce](./mobile/e-commerce/) | Магазин, Apple/Google Pay |
| [food-delivery](./mobile/food-delivery/) | Доставка, карта, real-time tracking |
| [fitness](./mobile/fitness/) | Здоровье, тренировки, HealthKit |
| [finance](./mobile/finance/) | Банк, инвестиции, биометрия |
| [social](./mobile/social/) | Соцсеть, лента, camera, stories |
| [task-manager](./mobile/task-manager/) | Задачи, offline-first, виджеты |
| [dating](./mobile/dating/) | Дейтинг, свайп, matching |
| [edtech](./mobile/edtech/) | Обучение, курсы, подписки |
| [marketplace](./mobile/marketplace/) | Объявления, чат, платежи |
| [news](./mobile/news/) | Новости, RSS, offline чтение |

## Desktop — типы приложений

| Тип | Описание |
|-----|----------|
| [notes](./desktop/notes/) | Заметки, Markdown, knowledge base |
| [ai-assistant](./desktop/ai-assistant/) | AI-ассистент, local LLM, hotkey |
| [messenger](./desktop/messenger/) | Мессенджер, tray, WebRTC |
| [media-player](./desktop/media-player/) | Аудио/видеоплеер, плейлисты |
| [file-manager](./desktop/file-manager/) | Файловый менеджер, dual-pane |
| [api-client](./desktop/api-client/) | REST/GraphQL клиент (как Postman) |
| [git-client](./desktop/git-client/) | Git GUI, граф коммитов, diff |
| [screen-recorder](./desktop/screen-recorder/) | Запись экрана, webcam, загрузка |
| [dashboard](./desktop/dashboard/) | Системный монитор, виджеты |
