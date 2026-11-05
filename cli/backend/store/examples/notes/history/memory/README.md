# history/memory

Память агентов по задачам.

Рабочие memory конкретной задачи хранятся по ролям:

```text
history/memory/<role>/<TASK_ID>.md
```

Рабочие role-директории: `analyst`, `architect`, `developer`, `tester`,
`reviewer`.
Developer дополнительно имеет workstreams:
`developer/backend`, `developer/frontend`, `developer/integration`.

Memory не заменяет report. Report описывает результат конкретного прохода, а
memory фиксирует reusable-понимание, patterns, ограничения и выводы для
следующих задач той же роли.
