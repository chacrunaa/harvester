# AGENTS.md

Единый entrypoint для агентных инструментов. Остальные файлы в корне
(`CLAUDE.md`, `CODEX.md`, `GEMINI.md`, `DEEPSEEK.md`,
`.github/copilot-instructions.md`) ссылаются сюда, чтобы инструкции не
расходились между копиями.

## Обязательная загрузка

1. `README.md` — стек, запуск, ограничения
2. `.ai/README.md` — устройство движка: агенты, навыки, карты маршрутов, фазы
3. `.ai/rules/pipeline.md` — универсальные правила конвейера
4. `.ai/rules/architecture.md` — архитектура и границы доменов
5. `.ai/rules/go-conventions.md` — Go-конвенции

## Source of truth — `.ai/`

- `.ai/agents/` — 17 промптов ролей и 16 карт маршрутов `*.route-map.json`
- `.ai/skills/` — 15 навыков, подгружаются в промпт по ссылке
- `.ai/rules/` — правила и конвенции
- `.ai/scripts/` — Go-модуль движка: watcher, запуск агента, клиент LLM
- `templates/ai/` — скелет `.ai/` для нового проекта (в корне, не внутри `.ai/`)

## Что важно знать про этот репозиторий

- Бэкенд — **Go + Gin + gorilla/websocket**, не Node.js. Фронтенд — React +
  Vite + MUI + TypeScript.
- **СУБД нет.** Состояние хранится атомарной записью JSON-файлов
  (`app/backend/internal/repository/atomic.go`). Правило
  `.ai/rules/database.md` описывает работу с БД для генерируемых
  проектов, а не для самого Harvester.
- Два Go-модуля: `app/backend` и `.ai/scripts`, связаны через `replace`,
  перечислены в `go.work`. Корень репозитория модулем не является,
  поэтому `go build ./...` из корня не работает — только внутри модулей.
- Watcher конвейера — библиотека, а не отдельный процесс: его поднимает
  бэкенд в `internal/service/watcher.go`.

## Runtime-каталоги

- `.claude/` — только обвязка платформы (hooks, permissions), не source of truth
- рабочие артефакты сессий не коммитятся
