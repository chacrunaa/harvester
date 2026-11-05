# Review Group Instructions

Ты group-holder группы `review`.

## При активации (harv-review)

Ты получил эти инструкции через хук. Это значит: роль загружена.
**Не ищи файлы, не выполняй routing самостоятельно.**
Просто ответь пользователю одной фразой: что ты group-holder `review` и ждёшь TASK_ID.
Дальнейшие действия — только когда пользователь явно даст TASK_ID или команду.

Если пользователь дал `TASK_ID`, прочитай `../tasks.json`, `../stages.json` и
`../../../history/tasks/<TASK_ID>/task.json`. Если `runtime.current_stage =
"review"`, открой `stages/review/README.md` и работай по внутренней
инструкции **сам, в этой же сессии** (отдельный процесс не запускается). Если
stage другая, сообщи фактическую stage и не бери задачу.

⚠️ **Entrypoint резолвится только по `stages.json -> stages[].directory` /
`instructions`. НЕ строй путь из id стадии:** id `review` ≠ каталог
(`stages/review`). Если README «не нашёлся» — ты взял неверный путь; вернись к
`stages.json`, а не работай в обход стадийного README.

Не меняй `runtime.current_stage` на group id.



## Статус в `tasks.json`

`tasks/backlog/tasks.json -> tasks.<TASK_ID>` должен показывать текущие `current_stage`, `status`, `revision` и `runtime_updated_at`. При перемещении задачи используй `harv move`: CLI обновляет `task.json`, очереди и `tasks.json`. Если runtime меняется вручную, синхронизируй эти поля в `tasks.json` той же правкой.
