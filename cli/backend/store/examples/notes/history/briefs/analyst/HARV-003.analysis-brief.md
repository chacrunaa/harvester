# HARV-003 analysis brief

Нужен API статусов синхронизации данных данных: queued, running, failed, completed.

Ожидаемый результат: backend хранит состояние, обновляет timestamps и возвращает последний статус по source_id.
