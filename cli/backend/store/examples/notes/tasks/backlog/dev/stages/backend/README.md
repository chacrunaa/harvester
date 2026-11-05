# backend

README для backend-разработчика стадии `backend`.

Детальная инструкция лежит в [`instructions.md`](instructions.md).

## Правило входа

Backend-разработчик берёт только задачи, у которых:

- `../../../../../history/tasks/<TASK_ID>/task.json -> runtime.current_stage = "backend"`;
- `TASK_ID` есть в `queue.json`;
- есть `../../../../../history/specifications/<TASK_ID>.developer-spec.md`;
- есть `../../../../../history/reports/architect/<TASK_ID>.architecture-report.md`.

## Результат стадии

- backend-изменения или явный backend no-op;
- `../../../../../history/reports/developer/backend/<TASK_ID>.backend-report.md`;
- `../../../../../history/memory/developer/backend/<TASK_ID>.md`;
- `../../../../../history/chats/developer/backend/<TASK_ID>.jsonl`;
- `result.json` ветки (`status`/`artifacts`/`questions`/`next_action`). Общий
  `task.json` ветка не двигает — артефакты регистрирует join `harv fanout`.

## Как исполняется ветка

Стадия запускается как ветка `harv fanout` (см.
[`../../instructions.md`](../../instructions.md)) — отдельным scripted run в
своём run-каталоге. Ветка не вызывает `harv take`/`harv move`/`harv advance`:
она пишет свои артефакты и возвращает `result.json`.

## Сигналы и failure path

- **happy path** — backend готов (или обоснованный `no_backend_changes`) →
  ветка возвращает `succeeded`.
- `blocked`/`failed` — нельзя продолжить (нет окружения, противоречие в
  spec/architecture): ветка возвращает `blocked`/`failed` + инцидент, причина — в
  backend report и JSON chat. Перезапуск — `harv retry <RUN_ID>`.

Запреты и детальный сценарий — в [`instructions.md`](instructions.md).

