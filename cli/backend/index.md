# backend/ — навигация

Движок и CLI второй версии Harvester. Python 3.11+, сторонних
зависимостей нет — только стандартная библиотека.

## Куда идти

| Область | Файл | О чём |
|---|---|---|
| Установка и команды | [README.md](README.md) | главный документ этого каталога |
| Роли и воркфлоу | [ai/README.md](ai/README.md) | агенты, навыки, адаптеры хуков |
| Контракт стадий | [store/examples/notes/tasks/backlog/stages.json](store/examples/notes/tasks/backlog/stages.json) | стадии, переходы, обязательные артефакты, правила записи |
| Карта репозитория | [../index.md](../index.md) | обе версии продукта |
| Entrypoint для агентов | [AGENTS.md](AGENTS.md) | `CLAUDE.md` ссылается на него |

## Пакеты

| Пакет | Путь | Назначение |
|---|---|---|
| `agentforge_notes` | `app/src/agentforge_notes/` | CLI `harv` (алиас `notes`) — 24 команды |
| `agentforge_launcher` | `app/src/agentforge_launcher/` | CLI `forge` (алиас `agentforge`) — выбор проекта, сборка промпта |

Точки входа объявлены в `pyproject.toml`. Скрипты `app/src/main` и
`app/src/forge` запускают те же CLI без установки пакета.

## Структура

```
backend/
  app/src/           два пакета + скрипты-обёртки
  app/tests/         65 тестов (unittest)
  ai/
    agents/          роли: бизнес-анализ, разработка, общий stage-worker
    skills/          business-analysis, notes-runtime
    workflows/       business-analysis, software-delivery
    adapters/        claude-hook, harv-gate — хуки Claude Code
  store/examples/notes/   скелет .notes/, копируется при harv init
  templates/         заготовка под будущие template init / template update
  projects/          симлинки на подключённые проекты (в git не попадают)
```

## Проверка

```bash
make check      # компиляция обоих пакетов + harv --help
make test       # 65 тестов
```
