// Сгенерировано .ai/scripts/cmd/pipeline-trace на реальном прогоне движка. Не редактировать вручную.
window.__ENGINE_RUN__ = {
  "events": [
    {
      "seq": 1,
      "kind": "pipeline_start",
      "phase": "init",
      "note": "задача DEMO-001, 16 агентов",
      "elapsed_ms": 0
    },
    {
      "seq": 2,
      "kind": "phase_active",
      "phase": "business",
      "note": "оркестратор фазы — product-manager",
      "elapsed_ms": 0
    },
    {
      "seq": 3,
      "kind": "agent_in-progress",
      "phase": "business",
      "agent": "product-analyst",
      "note": "параллельная ветка фазы business",
      "elapsed_ms": 0
    },
    {
      "seq": 4,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "pending",
        "frontend": "pending",
        "market-analyst": "pending",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "in-progress",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "pending"
      },
      "elapsed_ms": 301
    },
    {
      "seq": 5,
      "kind": "agent_in-progress",
      "phase": "business",
      "agent": "market-analyst",
      "note": "параллельная ветка фазы business",
      "elapsed_ms": 453
    },
    {
      "seq": 6,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "pending",
        "frontend": "pending",
        "market-analyst": "in-progress",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "in-progress",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "pending"
      },
      "elapsed_ms": 753
    },
    {
      "seq": 7,
      "kind": "agent_in-progress",
      "phase": "business",
      "agent": "strategist",
      "note": "параллельная ветка фазы business",
      "elapsed_ms": 905
    },
    {
      "seq": 8,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "pending",
        "frontend": "pending",
        "market-analyst": "in-progress",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "in-progress",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "in-progress"
      },
      "elapsed_ms": 1207
    },
    {
      "seq": 9,
      "kind": "agent_in-progress",
      "phase": "business",
      "agent": "financier",
      "note": "параллельная ветка фазы business",
      "elapsed_ms": 1356
    },
    {
      "seq": 10,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "in-progress",
        "frontend": "pending",
        "market-analyst": "in-progress",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "in-progress",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "in-progress"
      },
      "elapsed_ms": 1657
    },
    {
      "seq": 11,
      "kind": "agent_done",
      "phase": "business",
      "agent": "product-analyst",
      "note": "ветка завершена, AND-гейт ещё держит фазу",
      "elapsed_ms": 1808
    },
    {
      "seq": 12,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "in-progress",
        "frontend": "pending",
        "market-analyst": "in-progress",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "in-progress"
      },
      "elapsed_ms": 2109
    },
    {
      "seq": 13,
      "kind": "agent_done",
      "phase": "business",
      "agent": "market-analyst",
      "note": "ветка завершена, AND-гейт ещё держит фазу",
      "elapsed_ms": 2260
    },
    {
      "seq": 14,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "in-progress",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "in-progress"
      },
      "elapsed_ms": 2561
    },
    {
      "seq": 15,
      "kind": "agent_done",
      "phase": "business",
      "agent": "strategist",
      "note": "ветка завершена, AND-гейт ещё держит фазу",
      "elapsed_ms": 2712
    },
    {
      "seq": 16,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "in-progress",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 3013
    },
    {
      "seq": 17,
      "kind": "agent_done",
      "phase": "business",
      "agent": "financier",
      "note": "последняя ветка — AND-гейт открывается",
      "elapsed_ms": 3166
    },
    {
      "seq": 18,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "pending",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 3467
    },
    {
      "seq": 19,
      "kind": "agent_triggered",
      "agent": "business/product-manager",
      "note": "движок запросил запуск агента",
      "elapsed_ms": 3468
    },
    {
      "seq": 20,
      "kind": "agent_done",
      "phase": "business",
      "agent": "product-manager",
      "note": "оркестратор фазы business закончил: фаза может двигаться",
      "elapsed_ms": 3617
    },
    {
      "seq": 21,
      "kind": "state_changed",
      "phase": "business",
      "agents": {
        "analyst": "pending",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 3918
    },
    {
      "seq": 22,
      "kind": "phase_advanced",
      "from": "business",
      "to": "systemic",
      "note": "оркестратор фазы завершил работу",
      "elapsed_ms": 3919
    },
    {
      "seq": 23,
      "kind": "agent_triggered",
      "agent": "systemic/owner",
      "note": "движок запросил запуск агента",
      "elapsed_ms": 3920
    },
    {
      "seq": 24,
      "kind": "phase_active",
      "phase": "systemic",
      "note": "оркестратор фазы — owner",
      "elapsed_ms": 4068
    },
    {
      "seq": 25,
      "kind": "agent_in-progress",
      "phase": "systemic",
      "agent": "analyst",
      "note": "параллельная ветка фазы systemic",
      "elapsed_ms": 4069
    },
    {
      "seq": 26,
      "kind": "state_changed",
      "phase": "systemic",
      "agents": {
        "analyst": "in-progress",
        "architect": "pending",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 4370
    },
    {
      "seq": 27,
      "kind": "agent_in-progress",
      "phase": "systemic",
      "agent": "architect",
      "note": "параллельная ветка фазы systemic",
      "elapsed_ms": 4521
    },
    {
      "seq": 28,
      "kind": "state_changed",
      "phase": "systemic",
      "agents": {
        "analyst": "in-progress",
        "architect": "in-progress",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 4822
    },
    {
      "seq": 29,
      "kind": "agent_done",
      "phase": "systemic",
      "agent": "analyst",
      "note": "ветка завершена, AND-гейт ещё держит фазу",
      "elapsed_ms": 4972
    },
    {
      "seq": 30,
      "kind": "state_changed",
      "phase": "systemic",
      "agents": {
        "analyst": "done",
        "architect": "in-progress",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 5274
    },
    {
      "seq": 31,
      "kind": "agent_done",
      "phase": "systemic",
      "agent": "architect",
      "note": "последняя ветка — AND-гейт открывается",
      "elapsed_ms": 5424
    },
    {
      "seq": 32,
      "kind": "state_changed",
      "phase": "systemic",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "pending",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 5725
    },
    {
      "seq": 33,
      "kind": "agent_done",
      "phase": "systemic",
      "agent": "owner",
      "note": "оркестратор фазы systemic закончил: фаза может двигаться",
      "elapsed_ms": 5876
    },
    {
      "seq": 34,
      "kind": "state_changed",
      "phase": "systemic",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "pending",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 6177
    },
    {
      "seq": 35,
      "kind": "phase_advanced",
      "from": "systemic",
      "to": "development",
      "note": "оркестратор фазы завершил работу",
      "elapsed_ms": 6177
    },
    {
      "seq": 36,
      "kind": "agent_triggered",
      "agent": "development/dev-lead",
      "note": "движок запросил запуск агента",
      "elapsed_ms": 6177
    },
    {
      "seq": 37,
      "kind": "phase_active",
      "phase": "development",
      "note": "оркестратор фазы — dev-lead",
      "elapsed_ms": 6327
    },
    {
      "seq": 38,
      "kind": "agent_in-progress",
      "phase": "development",
      "agent": "backend",
      "note": "параллельная ветка фазы development",
      "elapsed_ms": 6328
    },
    {
      "seq": 39,
      "kind": "state_changed",
      "phase": "development",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "in-progress",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "pending",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 6629
    },
    {
      "seq": 40,
      "kind": "agent_in-progress",
      "phase": "development",
      "agent": "frontend",
      "note": "параллельная ветка фазы development",
      "elapsed_ms": 6779
    },
    {
      "seq": 41,
      "kind": "state_changed",
      "phase": "development",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "in-progress",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "in-progress",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 7080
    },
    {
      "seq": 42,
      "kind": "agent_done",
      "phase": "development",
      "agent": "backend",
      "note": "ветка завершена, AND-гейт ещё держит фазу",
      "elapsed_ms": 7230
    },
    {
      "seq": 43,
      "kind": "state_changed",
      "phase": "development",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "in-progress",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 7531
    },
    {
      "seq": 44,
      "kind": "agent_done",
      "phase": "development",
      "agent": "frontend",
      "note": "последняя ветка — AND-гейт открывается",
      "elapsed_ms": 7682
    },
    {
      "seq": 45,
      "kind": "state_changed",
      "phase": "development",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "pending",
        "strategist": "done"
      },
      "elapsed_ms": 7983
    },
    {
      "seq": 46,
      "kind": "agent_triggered",
      "agent": "development/reviewers",
      "note": "движок запросил запуск агента",
      "elapsed_ms": 7983
    },
    {
      "seq": 47,
      "kind": "agent_done",
      "phase": "development",
      "agent": "reviewers",
      "note": "запущен AND-гейтом фазы development",
      "elapsed_ms": 8135
    },
    {
      "seq": 48,
      "kind": "state_changed",
      "phase": "development",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "pending",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "done",
        "strategist": "done"
      },
      "elapsed_ms": 8437
    },
    {
      "seq": 49,
      "kind": "agent_done",
      "phase": "development",
      "agent": "dev-lead",
      "note": "оркестратор фазы development закончил: фаза может двигаться",
      "elapsed_ms": 8587
    },
    {
      "seq": 50,
      "kind": "state_changed",
      "phase": "development",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "done",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "pending",
        "qa-lead": "pending",
        "reviewers": "done",
        "strategist": "done"
      },
      "elapsed_ms": 8889
    },
    {
      "seq": 51,
      "kind": "phase_advanced",
      "from": "development",
      "to": "testing",
      "note": "оркестратор фазы завершил работу",
      "elapsed_ms": 8890
    },
    {
      "seq": 52,
      "kind": "agent_triggered",
      "agent": "testing/qa-lead",
      "note": "движок запросил запуск агента",
      "elapsed_ms": 8890
    },
    {
      "seq": 53,
      "kind": "phase_active",
      "phase": "testing",
      "note": "оркестратор фазы — qa-lead",
      "elapsed_ms": 9038
    },
    {
      "seq": 54,
      "kind": "agent_in-progress",
      "phase": "testing",
      "agent": "qa",
      "note": "параллельная ветка фазы testing",
      "elapsed_ms": 9039
    },
    {
      "seq": 55,
      "kind": "state_changed",
      "phase": "testing",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "done",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "pending",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "in-progress",
        "qa-lead": "pending",
        "reviewers": "done",
        "strategist": "done"
      },
      "elapsed_ms": 9340
    },
    {
      "seq": 56,
      "kind": "agent_in-progress",
      "phase": "testing",
      "agent": "penetration",
      "note": "параллельная ветка фазы testing",
      "elapsed_ms": 9491
    },
    {
      "seq": 57,
      "kind": "state_changed",
      "phase": "testing",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "done",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "in-progress",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "in-progress",
        "qa-lead": "pending",
        "reviewers": "done",
        "strategist": "done"
      },
      "elapsed_ms": 9792
    },
    {
      "seq": 58,
      "kind": "agent_done",
      "phase": "testing",
      "agent": "qa",
      "note": "ветка завершена, AND-гейт ещё держит фазу",
      "elapsed_ms": 9943
    },
    {
      "seq": 59,
      "kind": "state_changed",
      "phase": "testing",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "done",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "in-progress",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "done",
        "qa-lead": "pending",
        "reviewers": "done",
        "strategist": "done"
      },
      "elapsed_ms": 10244
    },
    {
      "seq": 60,
      "kind": "agent_done",
      "phase": "testing",
      "agent": "penetration",
      "note": "последняя ветка — AND-гейт открывается",
      "elapsed_ms": 10393
    },
    {
      "seq": 61,
      "kind": "state_changed",
      "phase": "testing",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "done",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "done",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "done",
        "qa-lead": "pending",
        "reviewers": "done",
        "strategist": "done"
      },
      "elapsed_ms": 10695
    },
    {
      "seq": 62,
      "kind": "agent_done",
      "phase": "testing",
      "agent": "qa-lead",
      "note": "оркестратор фазы testing закончил: фаза может двигаться",
      "elapsed_ms": 10846
    },
    {
      "seq": 63,
      "kind": "state_changed",
      "phase": "testing",
      "agents": {
        "analyst": "done",
        "architect": "done",
        "backend": "done",
        "dev-lead": "done",
        "financier": "done",
        "frontend": "done",
        "market-analyst": "done",
        "office-manager": "pending",
        "owner": "done",
        "penetration": "done",
        "product-analyst": "done",
        "product-manager": "done",
        "qa": "done",
        "qa-lead": "done",
        "reviewers": "done",
        "strategist": "done"
      },
      "elapsed_ms": 11148
    },
    {
      "seq": 64,
      "kind": "pipeline_complete",
      "note": "все фазы пройдены",
      "elapsed_ms": 11150
    },
    {
      "seq": 65,
      "kind": "agent_triggered",
      "agent": "office-manager",
      "note": "движок запросил запуск агента",
      "elapsed_ms": 11150
    }
  ],
  "phases": [
    "business",
    "systemic",
    "development",
    "testing"
  ],
  "subtitle": "Записан настоящим PipelineWatcher: порядок фаз, AND-гейты и переключение фаз — рабочий код. Вызовы LLM не выполнялись.",
  "task": "DEMO-001",
  "title": "Прогон движка конвейера"
};
