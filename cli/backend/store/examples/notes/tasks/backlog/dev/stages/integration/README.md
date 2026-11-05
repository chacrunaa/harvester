# integration

README для integration-gate стадии `integration`.

Детальная инструкция лежит в [`instructions.md`](instructions.md).

## Правило входа

Integration developer берёт только задачи, у которых:

- `../../../../../history/tasks/<TASK_ID>/task.json -> runtime.current_stage = "integration"`;
- `TASK_ID` есть в `queue.json`;
- есть backend report;
- есть frontend report.

## Результат стадии

- проверена связка backend/frontend/docs/swagger;
- создан общий `../../../../../history/reports/developer/<TASK_ID>.developer-report.md`;
- создан общий `../../../../../history/memory/developer/<TASK_ID>.md`;
- создан `../../../../../history/reports/developer/integration/<TASK_ID>.integration-report.md`;
- `result.json` ветки. Выход группы в `testing` делает group-holder через
  `harv advance` после join — не эта ветка.

## Как исполняется ветка

Стадия запускается как ветка `harv fanout` (см.
[`../../instructions.md`](../../instructions.md)) — отдельным scripted run в
своём run-каталоге. Ветка не вызывает `harv take`/`harv move`/`harv advance`:
она пишет свои артефакты и возвращает `result.json`.

> Зависимость: integration читает backend+frontend reports. При полном
> параллельном fan-out их ещё нет — см. предупреждение в
> [`../../README.md`](../../README.md).

## Сигналы и failure path

- **happy path** — связка backend/frontend/docs/swagger согласована →
  ветка возвращает `succeeded`; group-holder делает `harv advance --to testing`.
- `needs_adjustment`/`failed` — найдено расхождение: зафиксируй в integration
  report и верни ветку как `blocked`/`failed` + инцидент. Решение о re-fanout
  затронутых веток принимает group-holder (`strict` всё равно блокирует advance).
- `blocked` — нельзя проверить связку: ветка возвращает `blocked`, причина — в
  integration report.

Запреты и детальный сценарий — в [`instructions.md`](instructions.md).

