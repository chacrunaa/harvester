# Backlog Runtime

Backlog состоит из четырёх group-holder терминалов и восьми внутренних стадий:

| Group (keyword) | Internal stages | Назначение |
|---|---|---|
| `plan` (`harv-planning`) | `intake`, `analysis`, `architecture` | Intake, анализ и архитектурный handoff. |
| `dev` (`harv-dev`) | `backend`, `frontend`, `integration` | Последовательная developer-цепочка. |
| `testing` (`harv-testing`) | `testing` | Проверка результата и test report. |
| `review` (`harv-review`) | `review` | Финальный review и возвраты на доработку. |

Группа и стадия — разные сущности: `group` — это терминал (один из четырёх
keyword-ов выше), а `stage` (`stages[].id`) — конкретная роль внутри него.
Физический путь стадии берётся из `stages.json -> stages[].directory` и может не
совпадать с `id` (например, `id: analysis` лежит в `plan/stages/analysis`).

Навигационные файлы:

- `tasks.json` — лёгкий индекс задач и эпиков;
- `stages.json` — карта pipeline;
- `<group>/queue.json` — входная точка group-holder;
- `<group>/stages/<stage>/queue.json` — очередь конкретной внутренней стадии.

Полное состояние задачи хранится в `../../history/tasks/<TASK_ID>/task.json`.

Group-holder работает только со стадиями своей группы. Если задача находится в
другой группе, агент сообщает текущий `current_stage` и не берёт её в работу.
