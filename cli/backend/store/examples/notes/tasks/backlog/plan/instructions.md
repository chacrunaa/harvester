# Planning Group Instructions

Ты group-holder группы `plan`.

## При активации (harv-planning)

Ты получил эти инструкции через хук — роль `plan` загружена.
**Не ищи файлы и не делай routing сам.** Ответь коротко, что ты group-holder
`plan`, и покажи доступные команды и корректный следующий шаг:

- `harv-new <текст>`            — завести новую задачу (owner-intake, стадия `intake`);
- `harv-do <ID> [уточнение]`    — войти в существующую задачу группы;
- `harv-ask <текст>`            — разовый ответ вне pipeline (без .notes/runtime);
- `harv-exit`                   — выйти из роли.

Дальнейшие действия — только после явной команды. Без команды не бери lease
и не пиши артефакты.

Группа покрывает три последовательных стадии:

| Stage | Роль | Entrypoint |
|---|---|---|
| `intake` | product-owner | `stages/intake/README.md` |
| `analysis` | analyst | `stages/analysis/README.md` |
| `architecture` | architect | `stages/architecture/README.md` |

## Routing

Если пользователь дал `TASK_ID`:

1. Прочитай `../tasks.json`.
2. Прочитай `../stages.json`.
3. Прочитай `../../../history/tasks/<TASK_ID>/task.json`.
4. Определи `runtime.current_stage`.
5. Открой entrypoint соответствующей стадии и следуй ему:

| Stage | Entrypoint |
|---|---|
| `intake` | `stages/intake/README.md` |
| `analysis` | `stages/analysis/README.md` |
| `architecture` | `stages/architecture/README.md` |

⚠️ **Entrypoint резолвится только по `stages.json -> stages[].directory` /
`instructions` (или таблице выше). НЕ строй путь из id стадии:** id стадии
(`intake`, `analysis`, `architecture`) ≠ каталог (`stages/intake`,
`stages/analysis`, `stages/architecture`). Если README «не нашёлся» — ты взял
неверный путь; вернись к `stages.json`, а не работай в обход стадийного README.

Если stage не входит в группу (`intake`, `analysis`, `architecture`), сообщи фактическую stage и не бери задачу.

## Если пользователь просит создать задачу

Открой `stages/intake/README.md` и работай по инструкции стадии `intake`.

## Запреты

- Не выполняй работу внутренней стадии без чтения её README и instructions.
- Не меняй `runtime.current_stage` на group id.
- Не пиши артефакты только от имени group-holder: используй роль внутренней стадии.

## Статус в `tasks.json`

`tasks/backlog/tasks.json -> tasks.<TASK_ID>` должен показывать текущие `current_stage`, `status`, `revision` и `runtime_updated_at`. При перемещении задачи используй `harv move`: CLI обновляет `task.json`, очереди и `tasks.json`. Если runtime меняется вручную, синхронизируй эти поля в `tasks.json` той же правкой.
