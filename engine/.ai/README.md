# .ai/ — движок конвейера

Определения агентов, навыки, правила и Go-модуль движка. Рабочих данных
здесь нет: состояние конкретного проекта живёт в каталоге `.ai/` внутри
самого проекта и создаётся из `templates/ai/`.

---

## Структура

```
.ai/
├── agents/                      — 17 промптов ролей + 16 карт маршрутов
│   ├── office-manager.md        — инициализация, мониторинг, завершение
│   ├── business/
│   │   ├── product-manager.md   — оркестратор бизнес-фазы
│   │   ├── product-analyst.md   — бриф + БФТ
│   │   ├── market-analyst.md    — ЦА + конкуренты + рынок + инсайты
│   │   ├── strategist.md        — бизнес-модель + УТП + метрики
│   │   └── financier.md         — юнит-экономика + финмодель + MVP + CustDev
│   ├── systemic/
│   │   ├── owner.md             — оркестратор системной фазы, task-queue
│   │   ├── architect.md         — архитектурное ревью тех-предложения
│   │   └── analyst.md           — системный анализ, spec, clarifications
│   ├── development/
│   │   ├── dev-lead.md          — оркестратор разработки, цикл ревью
│   │   ├── backend.md           — серверная разработка
│   │   ├── frontend.md          — клиентская разработка
│   │   ├── reviewers.md         — code review
│   │   └── figma-designer.md    — вне конвейера, см. ниже
│   ├── testing/
│   │   ├── qa-lead.md           — оркестратор тестирования
│   │   ├── qa.md                — функциональное тестирование по AC
│   │   └── penetration.md       — penetration testing
│   └── **/*.route-map.json      — карты маршрутов: входы, выходы, куда копировать
│
├── skills/                      — 15 навыков, подгружаются в промпт по ссылке
│   ├── business/                — 13 инструкций для бизнес-аналитиков
│   │   ├── 01-product-brief.md … 13-market-insights.md
│   ├── systemic/
│   │   └── spec-format.md       — формат и правила написания spec.md
│   └── figma-designer/SKILL.md
│
├── rules/
│   ├── pipeline.md              — универсальные правила конвейера
│   ├── architecture.md          — архитектура, домены, границы
│   ├── go-conventions.md        — структура файлов, use case, handler
│   ├── database.md              — repository, SQL, транзакции
│   ├── frontend/                — архитектура, состояние, диалоги React
│   └── docs/                    — 23 правила написания документации
│
└── scripts/                     — Go-модуль harvester/scripts
    ├── pipeline-watcher.go      — fsnotify, порядок фаз, AND-гейт, маршрутизация
    ├── pipeline-state.go        — чтение и запись состояния конвейера
    ├── agent-runner.go          — запуск агента
    ├── lib/
    │   ├── context-builder.go   — сборка контекста по карте маршрутов
    │   ├── llm-client.go        — 4 провайдера, ретраи
    │   ├── response-parser.go   — разбор <file name="…">, поиск вопросов
    │   ├── file-io.go           — атомарная запись и копирование по маршруту
    │   └── docs-writer.go
    └── inits/init.go            — копирование скелета (не используется, см. ниже)
```

---

## Принципы

**Движок и рантайм разделены.** Этот каталог — неизменяемый движок, он
меняется только при разработке самого Harvester. У каждого проекта свой
рабочий каталог `.ai/`, который создаётся из `templates/ai/`.

**Файл как сообщение.** Агенты общаются только через файлы, прямых
вызовов агент → агент нет. `pipeline-watcher.go` замечает изменение через
`fsnotify` и запускает следующего агента.

**Маршрутизация.** Watcher копирует выходные файлы агента во входные
каталоги получателей по `*.route-map.json`. Агент пишет только в свой
каталог и о маршрутах не знает.

**AND-гейт.** Для фаз `business` и `development` следующий шаг
запускается лишь когда все параллельные агенты фазы получили статус
`done` в `pipeline-state.json`. Сама фаза переключается, когда завершил
работу её оркестратор.

**Навыки по ссылке.** `context-builder.go` ищет в промпте упоминания
вида `` `skills/*.md` `` и подкладывает эти файлы в контекст — список
навыков агента не дублируется в коде.

---

## Фазы конвейера

```
office-manager (init)
    ↓
[business]     product-manager → product-analyst, market-analyst,
                                 strategist, financier (параллельно)
                               → product-manager сводит результаты
    ↓
[systemic]     owner → analyst → (вопросы ↔ ответы с architect) → spec → owner
    ↓
[development]  dev-lead → backend, frontend (параллельно) → reviewers
                        → цикл, если REQUEST CHANGES
    ↓
[testing]      qa-lead → qa, penetration (параллельно)
    ↓
office-manager (finish)
```

Порядок фаз и состав гейтов заданы в `pipeline-watcher.go`
(`phaseOrder`, `phaseOrchestrators`, `andGates`). Состав агентов — в
`templates/ai/pipeline-state.json`.

---

## Запуск

Watcher — **не самостоятельная программа**, а библиотека. Его поднимает
Go-бэкенд внутри своего процесса
(`app/backend/internal/service/watcher.go`):

```bash
cd engine
make run        # бэкенд на :3100, watcher стартует вместе с ним
```

Новый проект создаётся через API бэкенда — `POST /api/projects/create`,
обработчик `app/backend/internal/transport/http/projects.go`. Он копирует
`templates/ai/` в `<проект>/.ai/` и заполняет `task_id` и `created_at` в
`pipeline-state.json`.

## Тесты

```bash
cd .ai/scripts && go test ./...     # 34 теста
```

Покрыты переходы фаз и AND-гейт, построение контекста по картам
маршрутов, разбор ответа LLM и атомарная запись файлов.

## Что здесь не используется

- **`figma-designer`** — есть промпт и навык, но нет карты маршрутов, и в
  `pipeline-state.json` этой роли нет. В конвейере не участвует.
- **`inits/init.go`** — экспортирует `Init(taskID, projectDir, harvesterRoot)`,
  но его никто не импортирует: ту же логику реализует обработчик
  `POST /api/projects/create`.
