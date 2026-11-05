# planning

Group-holder для intake, анализа и архитектурного review.

Внутренние стадии:

- `stages/intake` — product-owner, создаёт задачу из `draft.txt`;
- `stages/analysis` — analyst, анализирует и пишет developer specification;
- `stages/architecture` — architect, верифицирует spec и выдаёт architecture report.

Пользователь работает с этой группой как с одним терминалом. Group-holder берёт
задачи по stage id (`intake`, `analysis`, `architecture`), открывает
README соответствующей внутренней стадии и работает строго по её instructions.md.

Детальный routing описан в [`instructions.md`](instructions.md).
