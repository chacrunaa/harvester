# Copilot Instructions

Тонкий entrypoint для GitHub Copilot Chat.

## Обязательная загрузка

1. `.ai/README.md` — структура движка, агенты, фазы pipeline
2. `.ai/rules/pipeline.md` — универсальные правила pipeline
3. `.ai/rules/architecture.md` — архитектура и домены
4. `.ai/rules/go-conventions.md` — Go-конвенции
5. `.ai/rules/database.md` — работа с БД

## Source of truth — `.ai/`

- `.ai/agents/` — промпты всех агентов (14 ролей)
- `.ai/skills/` — инструкции выполнения задач
- `.ai/rules/` — правила и конвенции
- `.ai/scripts/` — pipeline-watcher и скрипты инициализации
- `.ai/templates/` — шаблоны для инициализации нового проекта

## Copilot runtime

- `.github/` — только platform wiring (instructions, workflows), не source of truth
