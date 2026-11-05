# chats/development/dev-lead

Оркестратор разработки. Управляет backend, frontend и review-циклом.

| Файл / Директория | Назначение |
|---|---|
| `experience.md` | накопленный опыт агента |
| `results/` | копии отчётов backend и frontend (Harvester маршрутизирует) |

Читает `results/backend.md` и `results/frontend.md`, запускает reviewers.
Если review = REQUEST CHANGES — повторяет цикл.
