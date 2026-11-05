# review

README для агента стадии `review`.

Стадия reviewer-а. Детальная инструкция лежит в
[`instructions.md`](instructions.md).

## Правило входа

Reviewer берёт только задачи, у которых:

- `../../../../../history/tasks/<TASK_ID>/task.json -> runtime.current_stage = "review"`;
- `TASK_ID` есть в `queue.json`;
- есть analyst, architect, developer и tester artifacts.

## Результат стадии

- accepted → задача переводится в `done`;
- code adjustment → задача возвращается в `backend`;
- architecture adjustment → задача возвращается в `architecture`;
- analysis adjustment → задача возвращается в `analysis`.

Reviewer не чинит код сам. Он принимает задачу или возвращает её с конкретным
brief-ом для нужной стадии.

## CLI стадии

```bash
harv take <TASK_ID> --stage review --owner reviewer
harv add-artifact <TASK_ID> --type report --path history/reports/reviewer/<TASK_ID>.review-report.md
harv add-artifact <TASK_ID> --type memory --path history/memory/reviewer/<TASK_ID>.md
# accepted:
harv move <TASK_ID> --to done --owner reviewer
# возвраты (с adjustment brief):
harv move <TASK_ID> --to backend --status needs_adjustment --owner reviewer
harv move <TASK_ID> --to architecture --status needs_adjustment --owner reviewer
harv move <TASK_ID> --to analysis --status needs_adjustment --owner reviewer
```

## Сигналы и failure path

- **happy path** (`accepted`) — все требования выполнены → `move ... --to done`.
- `code_adjustment` → возврат в `backend` с failure/adjustment brief.
- `architecture_adjustment` → возврат в `architecture` с adjustment brief.
- `analysis_adjustment` → возврат в `analysis` с adjustment brief.
- `blocked` — нельзя завершить review: `runtime.status = "blocked"`, задача
  остаётся в `review`.

Любой возврат сопровождается review report и adjustment brief для целевой
стадии. Запреты и детальный сценарий — в [`instructions.md`](instructions.md).
