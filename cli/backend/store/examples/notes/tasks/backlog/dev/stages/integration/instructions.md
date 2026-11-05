# Integration Developer Chat Instructions

Ты работаешь как integration gate стадии `integration`.

## Назначение

Твоя задача — проверить, что backend и frontend handoff согласованы, и собрать
единый developer handoff для тестировщика. Это последняя developer-стадия перед
`testing`.

## Перед началом

1. Прочитай `README.md`.
2. Прочитай `../../../tasks.json`.
3. Прочитай `../../../stages.json`.
4. Прочитай `../../../protocol.md`.
5. Прочитай `../../../runtime-schema.md`.
6. Прочитай `queue.json`.
7. Найди задачу по `task_id` в `../../../tasks.json` и проверь, что она есть в `queue.json`.
8. Прочитай `../../../../../history/tasks/<TASK_ID>/task.json`.
9. Убедись, что `runtime.current_stage = "integration"`.
10. Проверь `runtime.status`, `runtime.revision` и `runtime.lease`.
11. Прочитай `experience.json`.

Если задача в другой стадии или lease принадлежит другому активному агенту, не
бери её в работу.

## JSON chat

Пиши JSONL-записи в:

```text
../../../../../history/chats/developer/integration/<TASK_ID>.jsonl
```

Логируй чтение backend/frontend reports, contract checks, сборки/проверки,
создание integration report, общего developer report/memory и перевод в testing.

## Что читать

- `../../../../../history/specifications/<TASK_ID>.developer-spec.md`;
- `../../../../../history/reports/architect/<TASK_ID>.architecture-report.md`;
- `../../../../../history/reports/developer/backend/<TASK_ID>.backend-report.md`;
- `../../../../../history/reports/developer/frontend/<TASK_ID>.frontend-report.md`;
- `../../../../../history/memory/developer/backend/<TASK_ID>.md`;
- `../../../../../history/memory/developer/frontend/<TASK_ID>.md`;
- релевантные backend/frontend docs.

## Что проверить

- backend API contract совпадает с frontend usage;
- docs/specifications/swagger согласованы с кодом;
- permissions, error model и payload shape не расходятся;
- backend/frontend reports покрывают весь architecture route;
- no-op reports явно обоснованы;
- сборка/тесты по затронутым зонам выполнены или причина пропуска зафиксирована.

## Результат

Создай:

- `../../../../../history/reports/developer/integration/<TASK_ID>.integration-report.md`;
- `../../../../../history/reports/developer/<TASK_ID>.developer-report.md`;
- `../../../../../history/memory/developer/integration/<TASK_ID>.md`;
- `../../../../../history/memory/developer/<TASK_ID>.md`;
- при необходимости допиши
  `../../../../../history/chats/developer/integration/<TASK_ID>.jsonl`.

Integration report содержит contract-check details.

Общий developer report содержит итог всей developer-цепочки для tester:

- что сделал backend;
- что сделал frontend;
- какие no-op решения были приняты;
- какие документы/swagger обновлены;
- какие проверки запускались;
- что тестировщику проверять обязательно;
- остаточные риски.

Общая developer memory фиксирует reusable выводы всей developer-цепочки.

## Это ветка fan-out

Стадия `integration` исполняется как ветка параллельного `harv fanout`
(TASK-8). Выход группы в `testing` делает **group-holder** через
`harv advance` после сходимости join, а не эта ветка. Поэтому:

- Пиши **только** в свой run-каталог и свой integration report/memory — общий
  `task.json` ты не трогаешь и `harv move`/`harv advance` не вызываешь.
- Верни итог ветки структурно (`result.json`: `status`, `artifacts`,
  `questions`, `next_action`). Регистрацию артефактов и completion policy
  считает join-фаза `harv fanout`.

## Если найден developer-дефект

Не передавай задачу никуда сам. Зафиксируй проблему в integration report и верни
ветку как `blocked`/`failed` с инцидентом (`next_action: hold`). Решение о
повторном цикле (re-fanout затронутых веток через `harv retry` + новый
`harv fanout`) принимает group-holder — `strict`-политика всё равно не даст
`harv advance` выйти из группы, пока join не сошёлся.

## Запреты

- Не выходить в testing самому — это делает group-holder через `harv advance`.
- Не подменять общий integration report отдельными backend/frontend report.
- Не игнорировать mismatch между swagger/docs/frontend API usage.
- Не оставлять существенные действия только в ответе пользователю.
- Не двигать задачу и не писать в общий `task.json` — это делает join `harv fanout`.
