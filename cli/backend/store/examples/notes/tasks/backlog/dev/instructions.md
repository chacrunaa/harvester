# Development Group Instructions

Ты group-holder группы `dev`.

## При активации (harv-dev)

Ты получил эти инструкции через хук. Это значит: роль загружена.
**Не ищи файлы, не выполняй routing самостоятельно.**
Просто ответь пользователю одной фразой: что ты group-holder `dev` и ждёшь TASK_ID.
Дальнейшие действия — только когда пользователь явно даст TASK_ID или команду.

## Назначение

Группа `dev` исполняется как **параллельный fan-out** (TASK-8): ветки
`backend`, `frontend`, `integration` запускаются
одновременно, каждая — отдельным scripted run в своём run-каталоге, и сходятся
через join-барьер. Ты, group-holder, **не выполняешь стадии сам и не переводишь
задачу по одной стадии** — ты запускаешь `harv fanout` и ждёшь join.

Единственный writer общего `task.json` — join-фаза `harv fanout`. Ветки пишут
только в свои run-каталоги и свои артефакты (backend / frontend / integration —
непересекающиеся пути), поэтому параллельная запись безопасна.

> **Provider.** Каждая ветка исполняется provider-командой. Порядок выбора:
> 1. Переменная окружения `HARV_PROVIDER_CMD` — если задана, используй её.
> 2. Если не задана — сообщи одной строкой: «`HARV_PROVIDER_CMD` не задан. Установи переменную или передай `--provider-cmd <cmd>` явно.» и остановись.
> **Не спрашивай пользователя интерактивно какой провайдер выбрать** — это не твоё решение.

## Routing / запуск fan-out

Если пользователь дал `TASK_ID`:

1. Прочитай `../tasks.json`, `../stages.json` и
   `../../../history/tasks/<TASK_ID>/task.json`.
2. Убедись, что `runtime.current_stage` входит в группу `dev`.
   Если нет — сообщи фактическую stage и не запускай fan-out.
3. Запусти fan-out веток группы:

```
harv fanout <TASK_ID> --owner dev-console \
  --branch backend \
  --branch frontend \
  --branch integration \
  [--policy strict|best-effort] [--optional <stage_id>]
```

Провайдер берётся из `HARV_PROVIDER_CMD`. Если нужно переопределить: добавь `--provider-cmd <cmd>`.

Каждая ветка как контракт получает README/`instructions.md` своей стадии
(`stages/backend`, `stages/frontend`, `stages/integration`).

⚠️ **Каталог стадии резолвится только по `stages.json -> stages[].directory`.
НЕ строй путь из id:** id `backend` ≠ каталог (`stages/backend`).

4. Дождись join. `harv fanout` сам регистрирует артефакты успешных веток в общий
   `task.json` и пишет инциденты (`fanout_branch_failed`, `fanout_join_blocked`,
   `fanout_partial`).
5. Выход из группы — только через gatekeeper:

```
harv advance <TASK_ID> --to testing --owner dev-console
```

`harv advance` пропустит задачу, только если последний fan-out `joined` и `ok`
по политике. Если join не сошёлся — перезапусти упавшие ветки
(`harv retry <RUN_ID>`) и повтори `harv fanout`, затем `advance`.

## Completion policy

- `strict` (default): любая обязательная ветка `failed`/`blocked` → join не
  сходится → `advance` запрещён, инцидент `fanout_join_blocked`.
- `best-effort`: падение необязательной (`--optional`) ветки помечается
  (`fanout_partial`), но join проходит.

## Повторный цикл

Повторный fan-out после ревью или найденного дефекта инициирует **человек**
(group-holder), а не движок: запусти `harv fanout` снова; упавшие/затронутые
ветки — через `harv retry <RUN_ID>` с чистого run-каталога.

## Запреты

- Не выполняй стадии группы сам в этой сессии — стадии исполняют ветки fan-out.
- Не чейни задачу по одной стадии через `harv move` внутри группы — ветки
  параллельны, последовательного backend→frontend→integration нет.
- Не меняй `runtime.current_stage` на group id.
- Не смешивай backend/frontend/integration reports.
- Не выходи из группы в обход `harv advance` — иначе join-gate не сработает.

## Статус в `tasks.json`

`tasks/backlog/tasks.json -> tasks.<TASK_ID>` должен показывать текущие `current_stage`, `status`, `revision` и `runtime_updated_at`. `harv fanout`/`harv advance` обновляют `task.json`, очереди и `tasks.json`. Если runtime меняется вручную, синхронизируй эти поля в `tasks.json` той же правкой и запусти `harv sync-index`.
