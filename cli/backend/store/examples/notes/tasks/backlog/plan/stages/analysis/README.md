# analysis

README для агента стадии `analysis`.

Этот файл нужно читать первым при открытии консоли аналитика. Он объясняет, как
агент работает в контексте всей схемы `.notes/tasks`.

Детальный операционный чеклист стадии лежит в
[`instructions.md`](instructions.md). После чтения README агент обязан открыть
`instructions.md` и работать по нему.

## Общая схема

Runtime задач разделён на backlog-индексы и историю задач:

- `../../../tasks.json` — лёгкий индекс задач без полного runtime-состояния;
- `../../../stages.json` — карта pipeline, роли, статусы, обязательные входы и
  выходы, разрешённые переходы;
- `../../../<group>/stages/<stage>/queue.json` — очередь конкретной стадии;
- `../../../protocol.md` — общий протокол работы агентов;
- `../../../runtime-schema.md` — человекочитаемая схема runtime-файлов;
- `../../../../../history/tasks/<TASK_ID>/task.json` — полный runtime конкретной задачи;
- `../../../../../history/tasks/<TASK_ID>/source.txt` — исходное описание задачи;
- `../../../../../history/briefs`, `../../../../../history/specifications`,
  `../../../../../history/reports`, `../../../../../history/memory`, `../../../../../history/chats`,
  `../../../../../history/questions` — артефакты стадий.

`tasks.json` нужен для навигации. Фактическое состояние задачи проверяется в
`../../../../../history/tasks/<TASK_ID>/task.json -> runtime`.

## Место стадии

`analysis` получает задачу после intake-стадии `intake` и передаёт её в
`architecture`.

Вход стадии:

- задача есть в `../../../tasks.json`;
- задача есть в `queue.json`;
- `../../../../../history/tasks/<TASK_ID>/task.json -> runtime.current_stage = "analysis"`;
- есть `../../../../../history/tasks/<TASK_ID>/source.txt`.

Успешный выход стадии:

- создан `../../../../../history/briefs/analyst/<TASK_ID>.analysis-brief.md`;
- создан `../../../../../history/specifications/<TASK_ID>.developer-spec.md`;
- создан `../../../../../history/memory/analyst/<TASK_ID>.md`;
- `task.json -> artifacts` содержит ссылки на созданные артефакты;
- задача удалена из `queue.json`;
- задача добавлена в `../3-architecture/queue.json`;
- `task.json -> runtime.current_stage = "architecture"`;
- `task.json -> runtime.status = "ready_for_next_stage"`.

Если данных недостаточно, задача остаётся в `analysis` со статусом
`questions`, а вопросы фиксируются в `task.json -> questions` и
`task.json -> artifacts.questions`.

Если задача вернулась со статусом `needs_adjustment`, входным артефактом
считается один из brief-ов:

- `../../../../../history/briefs/architect/<TASK_ID>.analysis-adjustment-brief.md`;
- `../../../../../history/briefs/reviewer/<TASK_ID>.analysis-adjustment-brief.md`.

Файл вопросов создаётся по пути:

```text
../../../../../history/questions/analyst/<TASK_ID>.questions.md
```

В `task.json -> artifacts.questions` добавляется ссылка на этот файл. В
`task.json -> questions` добавляется структурированная запись с вопросами,
статусом `open` и пустыми ответами.

## Что читать перед задачей

Перед работой агент читает:

1. этот `README.md`;
2. `../../../protocol.md`;
3. `../../../runtime-schema.md`;
4. `../../../stages.json`;
5. `instructions.md`;
6. `experience.json`.

Когда пользователь даёт `TASK_ID`, например `HARV-123`, агент дополнительно
читает:

1. `../../../tasks.json`;
2. `queue.json`;
3. `../../../../../history/tasks/<TASK_ID>/task.json`;
4. `../../../../../history/tasks/<TASK_ID>/source.txt`.

## Граница README

README описывает только работу агента внутри структуры `.notes/tasks`: какие
файлы читать, где лежит состояние, как проверять стадию и куда переводить
задачу.

Что именно делать с содержанием задачи, как анализировать проектный контекст,
какие артефакты писать и как формулировать scope, описано в
[`instructions.md`](instructions.md).

## Правила записи

Состояние задачи предпочтительно менять через CLI:

```bash
harv status HARV-123
harv take HARV-123 --stage analysis --owner analysis-console
harv add-artifact HARV-123 --type brief --path history/briefs/analyst/HARV-123.analysis-brief.md
harv move HARV-123 --to architecture --owner analysis-console
```

Ручная правка JSON допустима только если CLI не покрывает нужный сценарий.
Перед любой ручной записью нужно перечитать `../../../../../history/tasks/<TASK_ID>/task.json`
и проверить, что `runtime.revision`, `runtime.current_stage` и `runtime.lease`
не изменились.

## Инварианты

- Агент берёт только задачи со стадии `analysis`.
- Нельзя менять `current_stage` без обязательных артефактов стадии.
- Нельзя удалять старые артефакты и историю задачи.
- Нельзя держать существенный результат только в ответе пользователю.
- Любое важное решение фиксируется в `.notes`.
