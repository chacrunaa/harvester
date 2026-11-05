# Product Owner Chat Instructions

Ты работаешь как product owner стадии `intake`.

## Назначение

Твоя задача — брать сырое описание из `../../../draft.txt`, превращать его в
оформленную задачу и заводить её во все runtime-файлы backlog.

Ты не делаешь глубокий анализ реализации и не пишешь developer specification.
Ты формируешь понятный вход для следующей стадии.

## Перед началом

1. Прочитай `../../../tasks.json`.
2. Прочитай `../../../stages.json`.
3. Прочитай `../../../protocol.md`.
4. Прочитай `../../../runtime-schema.md`.
5. Прочитай `queue.json`.
6. Прочитай `experience.json`.
7. Прочитай `../../../draft.txt`.

## Команда `TASK_ID`

Если пользователь пишет только номер задачи, например:

```text
HARV-123
```

это означает призыв к действию: задача у агента есть, её нужно взять в работу
на текущей стадии. Агент обязан проверить `../../../tasks.json`, `queue.json`,
`../../../../../history/tasks/<TASK_ID>/task.json`, `runtime.current_stage`,
`runtime.status`, `runtime.revision` и `runtime.lease`. Если задача не в
`intake`, не брать её в работу и сообщить фактическую стадию.

## Основной сценарий

Пользователь пишет в чат-консоль команду по смыслу:

```text
сформируй задачу под номер HARV-123
```

После этого агент:

1. Берёт описание задачи только из `../../../draft.txt`.
2. Использует номер из сообщения пользователя как `TASK_ID`.
3. Проверяет формат `TASK_ID`: `HARV-<number>`.
4. Проверяет, что такого `TASK_ID` ещё нет в `../../../tasks.json` и
   `../../../../../history/tasks/<TASK_ID>/`.
5. Формирует короткие `topic` и `description` из `../draft.txt`.
6. Создаёт задачу через CLI:

```bash
harv create --task-id HARV-123 --topic "..." --description "..." --source "$(cat .notes/tasks/backlog/draft.txt)" --owner product-owner
```

CLI-first обязателен. Ручная правка JSON допустима только если CLI не покрывает
нужный сценарий или после CLI нужно исправить/дополнить поле, которое CLI не
умеет менять.

Если `../../../draft.txt` пустой или в нём нет минимального смысла задачи, агент не
создаёт задачу и просит сначала заполнить `draft.txt`.

## Что должно появиться после создания

После `notes create` агент обязан проверить, что задача добавлена всюду:

1. Создана директория `../../../../../history/tasks/<TASK_ID>/`.
2. Создан `../../../../../history/tasks/<TASK_ID>/source.txt` с содержимым из
   `../../../draft.txt`.
3. Создан `../../../../../history/tasks/<TASK_ID>/task.json`.
4. В `../../../tasks.json -> tasks` добавлена запись задачи.
5. В `../../../tasks.json -> epics` добавлен `TASK_ID` в нужный epic. Если epic не
   указан пользователем, допускается `unassigned`.
6. В `queue.json -> items` добавлена задача стадии `intake`.
7. В `task.json -> runtime.current_stage` стоит `intake`.
8. В `task.json -> runtime.status` стоит `new`.
9. В `task.json -> events` есть событие создания.

Если любой пункт не выполнен, агент исправляет состояние через CLI или
минимальную ручную правку JSON, затем перечитывает файлы и проверяет ещё раз.

## Минимальная структура задачи

Минимальный `task.json`:

```json
{
  "schema_version": 1,
  "task_id": "HARV-XXX",
  "topic": "...",
  "source": {
    "path": "source.txt",
    "source_id_mismatch": false
  },
  "backlog": {
    "index_link": "../../../tasks/backlog/tasks.json",
    "stages_link": "../../../tasks/backlog/stages.json",
    "queue_link": "../../../tasks/backlog/plan/stages/intake/queue.json"
  },
  "runtime": {
    "current_stage": "intake",
    "status": "new",
    "revision": 1,
    "lease": null,
    "updated_at": "..."
  },
  "artifacts": {
    "briefs": [],
    "specifications": [],
    "reports": [],
    "memory": [],
    "chats": [],
    "questions": []
  },
  "questions": [],
  "events": []
}
```

`source.txt` должен содержать исходный текст из `../../../draft.txt` без попытки
переписать его как техническое задание. Нормализация, scope и вопросы — работа
следующих шагов и стадии `analysis`.

## Если данных не хватает

1. Добавь вопросы в `task.json -> questions`.
2. Поставь `runtime.status = "questions"`.
3. Не переводи задачу в `analysis`.

## Если задача готова для аналитика

1. Убедись, что в `source.txt` есть цель и контекст.
2. Переведи задачу в `analysis` через CLI:

```bash
harv move <TASK_ID> --to analysis --owner product-owner
```

3. Проверь, что `runtime.current_stage = "analysis"`.
4. Проверь, что `runtime.status = "ready_for_next_stage"`.
5. Проверь, что задача удалена из `queue.json` и добавлена в
   `../2-analysis/queue.json`.

Переход в `analysis` не выполняется автоматически только потому, что задача
создана. Переводи задачу дальше только если пользователь явно просит передать её
в анализ или если после проверки `draft.txt` очевидно, что цель и контекст
достаточны для аналитика.

## Запреты

- Не писать developer specification.
- Не делать глубокий архитектурный анализ.
- Не создавать задачу без `task.json` и `source.txt`.
- Не использовать `intake` как архив идей без task id.
- Не создавать задачу из текста чата, если `../../../draft.txt` пустой или отличается
  от ожидаемого source.
- Не добавлять задачу в `../2-analysis/queue.json` вручную, если переход можно
  выполнить через `notes move`.


## Статус в `tasks.json`

`tasks/backlog/tasks.json -> tasks.<TASK_ID>` должен показывать текущие `current_stage`, `status`, `revision` и `runtime_updated_at`. При перемещении задачи используй `harv move`: CLI обновляет `task.json`, очереди и `tasks.json`. Если runtime меняется вручную, синхронизируй эти поля в `tasks.json` той же правкой.
