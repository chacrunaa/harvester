// Сгенерировано tools/trace-cli.py на реальном прогоне CLI. Не редактировать вручную.
window.__CLI_RUN__ = {
  "title": "Реальный прогон harv",
  "subtitle": "Записан автоматически. Ключи LLM не нужны: harv не ходит в сеть.",
  "task": "HARV-004",
  "steps": [
    {
      "label": "init",
      "command": "harv init <project> --personal",
      "note": "создаёт .notes/ из store/examples/notes и подключает проект",
      "ok": true,
      "exit": 0,
      "output": "code-roots: backend=backend ui=frontend docs=documentations\nинициализирован: /private/var/folders/82/jm3x8r3d0cq0gjcv14tttnmh0000gn/T/harv-trace-g913kh3t/demo-project/.notes\nзарегистрирован: projects/personal/demo-project → /private/var/folders/82/jm3x8r3d0cq0gjcv14tttnmh0000gn/T/harv-trace-g913kh3t/demo-project\nактивный проект: personal/demo-project",
      "runtime": {},
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "create",
      "command": "harv create \"Добавить экспорт отчётов в CSV\"",
      "note": "задача HARV-004 заходит в стадию intake",
      "ok": true,
      "exit": 0,
      "output": "created HARV-004 in intake",
      "runtime": {
        "stage": "intake",
        "status": "new",
        "revision": 1,
        "owner": null,
        "artifacts": 6,
        "events": 1
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ]
      }
    },
    {
      "label": "status",
      "command": "harv status HARV-004",
      "note": "состояние задачи: стадия, статус, ревизия",
      "ok": true,
      "exit": 0,
      "output": "{\n  \"task_id\": \"HARV-004\",\n  \"topic\": \"Добавить экспорт отчётов в CSV\",\n  \"stage\": \"intake\",\n  \"status\": \"new\",\n  \"revision\": 1,\n  \"lease\": null,\n  \"artifacts\": {\n    \"briefs\": [],\n    \"specifications\": [],\n    \"reports\": [],\n    \"memory\": [],\n    \"chats\": [],\n    \"questions\": []\n  }\n}",
      "runtime": {
        "stage": "intake",
        "status": "new",
        "revision": 1,
        "owner": null,
        "artifacts": 6,
        "events": 1
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ]
      }
    },
    {
      "label": "take",
      "command": "harv take HARV-004 --stage intake --owner planning-terminal",
      "note": "агент берёт задачу — ставится lease на 120 минут",
      "ok": true,
      "exit": 0,
      "output": "taken HARV-004 in intake by planning-terminal",
      "runtime": {
        "stage": "intake",
        "status": "in_progress",
        "revision": 2,
        "owner": "planning-terminal",
        "artifacts": 6,
        "events": 2
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ]
      }
    },
    {
      "label": "advance-analysis",
      "command": "harv advance HARV-004 --to analysis",
      "note": "валидирующая передача: переход сверяется с картой стадий",
      "ok": true,
      "exit": 0,
      "output": "advanced HARV-004: intake -> analysis (ready_for_next_stage)\nreport: history/handoffs/HARV-004/EVT-HARV-004-001.json",
      "runtime": {
        "stage": "analysis",
        "status": "ready_for_next_stage",
        "revision": 3,
        "owner": null,
        "artifacts": 6,
        "events": 3
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "gate-blocked",
      "command": "harv advance HARV-004 --to architecture",
      "note": "ГЕЙТ сработал: стадия analysis обязана оставить 3 артефакта — передача отклонена",
      "ok": false,
      "exit": 1,
      "output": "handoff blocked: HARV-004 analysis -> architecture\n  [required_output_missing] missing output file: history/briefs/analyst/HARV-004.analysis-brief.md -> создайте обязательный артефакт\n  [required_output_missing] missing output file: history/specifications/HARV-004.developer-spec.md -> создайте обязательный артефакт\n  [required_output_missing] missing output file: history/memory/analyst/HARV-004.md -> создайте обязательный артефакт",
      "runtime": {
        "stage": "analysis",
        "status": "ready_for_next_stage",
        "revision": 3,
        "owner": null,
        "artifacts": 6,
        "events": 3
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "artifacts-added",
      "command": "harv artifacts HARV-004",
      "note": "агент выложил 3 обязательных артефакта и зарегистрировал их через add-artifact",
      "ok": true,
      "exit": 0,
      "output": "[ok ] reports: history/briefs/analyst/HARV-004.analysis-brief.md\n[ok ] reports: history/specifications/HARV-004.developer-spec.md\n[ok ] reports: history/memory/analyst/HARV-004.md",
      "runtime": {
        "stage": "analysis",
        "status": "ready_for_next_stage",
        "revision": 6,
        "owner": null,
        "artifacts": 6,
        "events": 6
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "advance-architecture",
      "command": "harv advance HARV-004 --to architecture",
      "note": "теперь гейт пропускает: требуемые артефакты на месте и зарегистрированы",
      "ok": true,
      "exit": 0,
      "output": "advanced HARV-004: analysis -> architecture (ready_for_next_stage)\nreport: history/handoffs/HARV-004/EVT-HARV-004-003.json",
      "runtime": {
        "stage": "architecture",
        "status": "ready_for_next_stage",
        "revision": 7,
        "owner": null,
        "artifacts": 6,
        "events": 7
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "architecture": [
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "revision-conflict",
      "command": "harv advance HARV-004 --to backend --expect-revision 999",
      "note": "конфликт ревизий: ожидали 999, в файле другая — чужая работа не перезаписывается",
      "ok": false,
      "exit": 1,
      "output": "handoff blocked: HARV-004 architecture -> backend\n  [stale_revision] expected revision 999, got 9 -> перечитайте task.json и повторите",
      "runtime": {
        "stage": "architecture",
        "status": "ready_for_next_stage",
        "revision": 9,
        "owner": null,
        "artifacts": 6,
        "events": 9
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "architecture": [
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "advance-dev",
      "command": "harv advance HARV-004 --to backend",
      "note": "с корректной ревизией задача уходит в группу dev",
      "ok": true,
      "exit": 0,
      "output": "advanced HARV-004: architecture -> backend (ready_for_next_stage)\nreport: history/handoffs/HARV-004/EVT-HARV-004-005.json",
      "runtime": {
        "stage": "backend",
        "status": "ready_for_next_stage",
        "revision": 10,
        "owner": null,
        "artifacts": 6,
        "events": 10
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "fanout",
      "command": "harv fanout HARV-004 --branch backend --branch frontend --policy strict",
      "note": "fanout создаёт группу ветвей и ставит барьер: при strict соединение не произойдёт, пока обе ветки не отчитаются. Здесь ветки не запускались — для их исполнения нужен провайдер LLM, поэтому барьер честно отказывает",
      "ok": false,
      "exit": 1,
      "output": "error: fanout GRP-HARV-004-001 blocked (strict): required branches not succeeded: backend, frontend\nnext: перезапустите упавшие ветки: harv retry <RUN_ID>, затем повторите fanout",
      "runtime": {
        "stage": "backend",
        "status": "ready_for_next_stage",
        "revision": 11,
        "owner": null,
        "artifacts": 6,
        "events": 14
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "queues",
      "command": "harv queues",
      "note": "очереди по стадиям: какой чат что может взять",
      "ok": true,
      "exit": 0,
      "output": "intake                 [product-owner] HARV-001\nanalysis               [analyst] HARV-002\narchitecture           [architect] —\nbackend                [backend-developer] HARV-003, HARV-004\nfrontend               [frontend-developer] —\nintegration            [integration-developer] —\ntest                   [tester] —\nreview                 [reviewer] —",
      "runtime": {
        "stage": "backend",
        "status": "ready_for_next_stage",
        "revision": 11,
        "owner": null,
        "artifacts": 6,
        "events": 14
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    },
    {
      "label": "validate",
      "command": "harv validate",
      "note": "проверка целостности .notes/",
      "ok": true,
      "exit": 0,
      "output": "validation ok",
      "runtime": {
        "stage": "backend",
        "status": "ready_for_next_stage",
        "revision": 11,
        "owner": null,
        "artifacts": 6,
        "events": 14
      },
      "queues": {
        "backend": [
          "{'task_id': 'HARV-003', 'task_link': '../../../../../history/tasks/HARV-003/task.json', 'priority': 30}",
          "{'task_id': 'HARV-004', 'task_link': '../../../../../history/tasks/HARV-004/task.json', 'priority': 100}"
        ],
        "analysis": [
          "{'task_id': 'HARV-002', 'task_link': '../../../../../history/tasks/HARV-002/task.json', 'priority': 20}"
        ],
        "intake": [
          "{'task_id': 'HARV-001', 'task_link': '../../../../../history/tasks/HARV-001/task.json', 'priority': 10}"
        ]
      }
    }
  ]
};
