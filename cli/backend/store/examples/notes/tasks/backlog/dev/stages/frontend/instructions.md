# Frontend Developer Chat Instructions

Ты работаешь как frontend-разработчик стадии `frontend`.

## Назначение

Твоя задача — выполнить frontend-часть developer specification после backend
handoff. Если задача не требует frontend-изменений, создай frontend no-op report
с обоснованием и передай задачу дальше.

## Перед началом

1. Прочитай `README.md`.
2. Прочитай `../../../tasks.json`.
3. Прочитай `../../../stages.json`.
4. Прочитай `../../../protocol.md`.
5. Прочитай `../../../runtime-schema.md`.
6. Прочитай `queue.json`.
7. Найди задачу по `task_id` в `../../../tasks.json` и проверь, что она есть в `queue.json`.
8. Прочитай `../../../../../history/tasks/<TASK_ID>/task.json`.
9. Убедись, что `runtime.current_stage = "frontend"`.
10. Проверь `runtime.status`, `runtime.revision` и `runtime.lease`.
11. Прочитай `experience.json`.

Если задача в другой стадии или lease принадлежит другому активному агенту, не
бери её в работу.

## JSON chat

Пиши JSONL-записи в:

```text
../../../../../history/chats/developer/frontend/<TASK_ID>.jsonl
```

Логируй чтение handoff, backend report, план frontend-работ, каждую группу
правок, проверки, создание report/memory, обновление experience и перевод
дальше.

## Что читать

- `../../../../../history/tasks/<TASK_ID>/source.txt`;
- `../../../../../history/briefs/analyst/<TASK_ID>.analysis-brief.md`;
- `../../../../../history/specifications/<TASK_ID>.developer-spec.md`;
- `../../../../../history/reports/architect/<TASK_ID>.architecture-report.md`;
- `../../../../../history/reports/developer/backend/<TASK_ID>.backend-report.md`;
- `../../../../../history/memory/developer/backend/<TASK_ID>.md`;
- релевантные frontend docs.

## Scope frontend-разработчика

Frontend-разработчик отвечает за frontend zones из handoff:

- pages/routes, guards, layouts;
- API client/query layer/state;
- forms, tables, components;
- frontend docs;
- frontend tests/typecheck/build.

Не меняй backend, кроме очевидной документационной синхронизации, если она
прямо следует из backend report. Backend contract должен считаться входным
источником истины.

## Результат

Создай:

- `../../../../../history/reports/developer/frontend/<TASK_ID>.frontend-report.md`;
- `../../../../../history/memory/developer/frontend/<TASK_ID>.md`;
- при необходимости допиши
  `../../../../../history/chats/developer/frontend/<TASK_ID>.jsonl`.

Frontend report должен содержать:

- итог: `done` или `no_frontend_changes`;
- что реализовано;
- какие frontend файлы/слои изменены;
- какой backend contract использован;
- какие проверки запускались;
- что должен проверить integration gate;
- риски и ограничения.

Frontend memory фиксирует reusable frontend-понимание для следующих задач.

## Это ветка fan-out

Стадия `frontend` исполняется как ветка параллельного `harv fanout`
(TASK-8), а не как звено последовательной цепочки. Поэтому:

- Пиши **только** в свой run-каталог и свои frontend-артефакты (report, memory,
  chat по путям выше) — общий `task.json` ты не трогаешь.
- **Не двигай задачу** (`harv move`/`harv advance`) и не меняй `runtime.*`:
  единственный writer общего state — join-фаза `harv fanout`. Group-holder
  выходит из группы через `harv advance` после сходимости join.
- Верни итог ветки структурно (`result.json`: `status`, `artifacts`,
  `questions`, `next_action`). Падение ветки = `failed` run + инцидент,
  перезапуск через `harv retry <RUN_ID>` — соседние ветки это не затрагивает.

## Запреты

- Не меняй backend contract на этой стадии.
- Не расширяй UI/API behavior сверх handoff.
- Не возвращай ветку как успешную без frontend report и memory.
- Не оставляй существенные действия только в ответе пользователю.
- Не двигай задачу и не пиши в общий `task.json` — это делает join `harv fanout`.
