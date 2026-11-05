# history/chats

Legacy/aggregate зона.

Рабочие логи чатов конкретной задачи теперь хранятся рядом с задачей:

```text
history/chats/<role>/
```

Рабочие role-директории: `analyst`, `architect`, `developer`, `tester`,
`reviewer`.
Developer дополнительно имеет workstreams:
`developer/backend`, `developer/frontend`, `developer/integration`.

В эту директорию можно складывать только сводные cross-task chat exports, если они понадобятся позже.
