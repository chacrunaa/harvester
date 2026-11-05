# testing

README для агента стадии `testing`.

Стадия тестировщика. Детальная инструкция лежит в
[`instructions.md`](instructions.md).

## Правило входа

Тестировщик берёт только задачи, у которых:

- `../../../../../history/tasks/<TASK_ID>/task.json -> runtime.current_stage = "testing"`;
- `TASK_ID` есть в `queue.json`;
- есть developer specification и developer report.

## Результат стадии

- test instruction, SQL scripts и `.ch` scripts;
- полный terminal evidence;
- `../../../../../history/reports/tester/<TASK_ID>.test-report.md`;
- `../../../../../history/memory/tester/<TASK_ID>.md`;
- manual test-case в `new-app/documentations/docs/06-quality/test-cases`;
- запись в `new-app/documentations/docs/06-quality/test-reports/result.md`;
- если всё прошло — перевод задачи в `review`;
- если проверка провалена — failure brief и возврат задачи в `backend`.

## CLI стадии

```bash
harv take <TASK_ID> --stage testing --owner tester
harv add-artifact <TASK_ID> --type report --path history/reports/tester/<TASK_ID>.test-report.md
harv add-artifact <TASK_ID> --type report --path history/reports/tester/<TASK_ID>.test-instruction.md
harv add-artifact <TASK_ID> --type memory --path history/memory/tester/<TASK_ID>.md
# проверка пройдена:
harv move <TASK_ID> --to review --owner tester
# проверка провалена:
harv move <TASK_ID> --to backend --status needs_adjustment --owner tester
```

## Сигналы и failure path

- **happy path** (`passed`) — все проверки зелёные с evidence → `move ... --to review`.
- `needs_adjustment` (`failed`) — создай failure/adjustment brief с воспроизведением
  и верни задачу в `backend` со статусом `needs_adjustment`.
- `blocked` — невозможно прогнать проверки (нет окружения/данных):
  `runtime.status = "blocked"`, задача остаётся в `testing`, точная команда и
  причина — в test report и `*.terminal.log`.

Детальный сценарий — в [`instructions.md`](instructions.md).
