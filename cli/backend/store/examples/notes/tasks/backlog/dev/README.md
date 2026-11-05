# development

Group-holder developer-группы. Стадии исполняются как параллельный fan-out
(TASK-8) через `harv fanout` + join, выход — через `harv advance`. См.
[`instructions.md`](instructions.md).

Ветки (внутренние стадии):

- `stages/backend`;
- `stages/frontend`;
- `stages/integration`.

Пользователь работает с этой группой как с одним development-терминалом.
Group-holder запускает fan-out веток и ждёт join, не выполняя стадии сам.

> ⚠️ **Зависимости веток.** Контракты стадий предполагают, что frontend читает
> backend report, а integration — backend+frontend reports. Это data-dependency,
> несовместимая с одновременным запуском всех трёх веток. Перед полным
> параллельным fan-out согласуй стратегию (полный параллельный vs
> dependency-aware: независимые ветки параллельно, зависимые — следующим fan-out).

