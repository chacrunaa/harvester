# architecture

README для агента стадии `architecture`.

Стадия архитектора. Детальная инструкция лежит в
[`instructions.md`](instructions.md).

## Место стадии

`architecture` получает задачу после `analysis` и передаёт её в
`backend`.

Архитектор проверяет архитектурные решения аналитика: границы слоёв, ownership,
контракты, документацию, expected changes и риски. Если в analyst artifacts
чего-то не хватает, архитектор дополняет developer specification и brief.

## Правило входа

Архитектор берёт только задачи, у которых:

- `../../../../../history/tasks/<TASK_ID>/task.json -> runtime.current_stage = "architecture"`;
- `TASK_ID` есть в `queue.json`;
- есть `../../../../../history/briefs/analyst/<TASK_ID>.analysis-brief.md`;
- есть `../../../../../history/specifications/<TASK_ID>.developer-spec.md`;
- есть `../../../../../history/memory/analyst/<TASK_ID>.md`.

Если задача вернулась из review со статусом `needs_adjustment` именно в
`architecture`, входным артефактом считается
`../../../../../history/briefs/reviewer/<TASK_ID>.architecture-adjustment-brief.md`.

## Результат стадии

Успешный выход:

- analyst brief и developer specification проверены;
- при необходимости analyst brief и developer specification дополнены;
- создан `../../../../../history/reports/architect/<TASK_ID>.architecture-report.md`;
- создан `../../../../../history/memory/architect/<TASK_ID>.md`;
- при необходимости дописан `../../../../../history/chats/architect/<TASK_ID>.jsonl`;
- задача переведена в `backend`.

Если архитектурно нельзя подтвердить handoff, задача возвращается в
`analysis`:

- создан `../../../../../history/briefs/architect/<TASK_ID>.analysis-adjustment-brief.md`;
- создан `../../../../../history/reports/architect/<TASK_ID>.architecture-report.md`;
- `runtime.status = "needs_adjustment"`;
- задача переведена обратно в `analysis`.

## CLI стадии

```bash
harv take <TASK_ID> --stage architecture --owner architect
harv add-artifact <TASK_ID> --type report --path history/reports/architect/<TASK_ID>.architecture-report.md
harv add-artifact <TASK_ID> --type memory --path history/memory/architect/<TASK_ID>.md
# handoff:
harv move <TASK_ID> --to backend --owner architect
# возврат на доработку анализа:
harv move <TASK_ID> --to analysis --status needs_adjustment --owner architect
```

## Сигналы и failure path

- **happy path** — handoff подтверждён → `move ... --to backend`.
- `analysis_adjustment` — handoff нельзя подтвердить: создай
  `history/briefs/architect/<TASK_ID>.analysis-adjustment-brief.md` и верни задачу
  в `analysis` со статусом `needs_adjustment`.
- `blocked` — архитектурно нельзя продолжить: `runtime.status = "blocked"`,
  задача остаётся в `architecture`.

Детальный сценарий — в [`instructions.md`](instructions.md).
