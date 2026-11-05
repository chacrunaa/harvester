# Harvester v2 — индекс

Вторая версия продукта: вместо сервера с веб-интерфейсом — CLI `harv`,
который ведёт задачу по стадиям, а роли исполняют агенты в чатах
Claude Code или Codex.

## Что где

| Каталог | Содержимое |
|---|---|
| [`backend/`](backend/README.md) | движок и CLI: Python, без сторонних зависимостей |
| [`backend/app/src/agentforge_notes/`](backend/app/src/agentforge_notes/) | CLI `harv` — 24 команды |
| [`backend/app/src/agentforge_launcher/`](backend/app/src/agentforge_launcher/) | CLI `forge` — выбор проекта и сборка промпта |
| [`backend/ai/`](backend/ai/README.md) | роли агентов, навыки, воркфлоу, адаптеры хуков |
| [`backend/store/examples/notes/`](backend/store/examples/notes/) | скелет `.notes/`, копируется при `harv init` |
| [`backend/app/tests/`](backend/app/tests/) | 65 тестов на `unittest` |

## Чем отличается от v1

| | v1 (`engine/`) | v2 (`cli/`) |
|---|---|---|
| Стек | Go + Gin + WebSocket, React + Vite | Python 3.11+, только стандартная библиотека |
| Интерфейс | веб-приложение | CLI + чаты агентов |
| Запуск агента | движок сам вызывает LLM по HTTP | роль активируется ключевым словом в чате |
| Состояние | `.ai/pipeline-state.json` в проекте | `.notes/` в проекте |
| Единица работы | 4 фазы, 16 ролей | 8 стадий, 4 группы ролей |

## С чего начать

1. [`backend/README.md`](backend/README.md) — установка, команды, стадии, роли.
2. [`backend/store/examples/notes/tasks/backlog/stages.json`](backend/store/examples/notes/tasks/backlog/stages.json) —
   контракт целиком: стадии, переходы, обязательные артефакты, правила записи.
   Это и есть источник правды, а не описание рядом с ним.
3. [`backend/ai/`](backend/ai/README.md) — роли и воркфлоу.
4. [`../ui/cli.html`](../ui/cli.html) — записанный прогон задачи в витрине.
