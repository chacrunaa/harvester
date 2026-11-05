# frontend

README для frontend-разработчика стадии `frontend`.

Детальная инструкция лежит в [`instructions.md`](instructions.md).

## Правило входа

Frontend-разработчик берёт только задачи, у которых:

- `../../../../../history/tasks/<TASK_ID>/task.json -> runtime.current_stage = "frontend"`;
- `TASK_ID` есть в `queue.json`;
- есть `../../../../../history/specifications/<TASK_ID>.developer-spec.md`;
- есть `../../../../../history/reports/architect/<TASK_ID>.architecture-report.md`;
- есть `../../../../../history/reports/developer/backend/<TASK_ID>.backend-report.md`.

## Результат стадии

- frontend-изменения или явный frontend no-op;
- `../../../../../history/reports/developer/frontend/<TASK_ID>.frontend-report.md`;
- `../../../../../history/memory/developer/frontend/<TASK_ID>.md`;
- `../../../../../history/chats/developer/frontend/<TASK_ID>.jsonl`;
- `result.json` ветки (`status`/`artifacts`/`questions`/`next_action`). Общий
  `task.json` ветка не двигает — артефакты регистрирует join `harv fanout`.

## Как исполняется ветка

Стадия запускается как ветка `harv fanout` (см.
[`../../instructions.md`](../../instructions.md)) — отдельным scripted run в
своём run-каталоге. Ветка не вызывает `harv take`/`harv move`/`harv advance`:
она пишет свои артефакты и возвращает `result.json`.

> Зависимость: контракт стадии предполагает наличие backend report. При полном
> параллельном fan-out его ещё нет — см. предупреждение в
> [`../../README.md`](../../README.md).

## Сигналы и failure path

- **happy path** — frontend готов (или обоснованный `no_frontend_changes`) →
  ветка возвращает `succeeded`.
- `blocked`/`failed` — нельзя продолжить: ветка возвращает `blocked`/`failed` +
  инцидент, причина — в frontend report и JSON chat. Перезапуск — `harv retry <RUN_ID>`.

Запреты и детальный сценарий — в [`instructions.md`](instructions.md).

