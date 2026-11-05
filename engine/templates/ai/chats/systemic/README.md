# chats/systemic

Фаза системного анализа. Owner и architect работают параллельно, analyst — по задачам owner.

```
systemic/
├── brief-business.md   — бриф из бизнес-фазы (копирует Harvester)
├── brief-systemic.md   — итоговый системный бриф (пишет owner)
├── diff.md             — расхождения между предложениями
├── chat.json           — история диалогов фазы
├── owner/              — оркестратор + task-queue для analyst
├── architect/          — архитектурное ревью тех-предложения
└── analyst/            — системный анализ по задачам owner
```
