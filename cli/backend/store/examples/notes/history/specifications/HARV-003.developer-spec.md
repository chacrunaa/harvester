# HARV-003 developer spec

Реализовать backend endpoint `GET /api/sources/{source_id}/sync-status` и внутреннее хранилище статуса.

Минимальные проверки: неизвестный source_id, failed с текстом ошибки, completed с временем завершения.
