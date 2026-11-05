# history/reports

Legacy/aggregate зона.

Рабочие отчёты конкретной задачи теперь хранятся рядом с задачей:

```text
history/reports/<role>/
```

Рабочие role-директории: `architect`, `developer`, `tester`, `reviewer`.
Developer дополнительно имеет workstreams:
`developer/backend`, `developer/frontend`, `developer/integration`.

В эту директорию можно складывать только сводные cross-task отчёты, если они понадобятся позже.
