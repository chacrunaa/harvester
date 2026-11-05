from .clock import now_iso


def add_event(task, event_type, stage, status, note=None, actor=None):
    events = task.setdefault("events", [])
    item = {
        "at": now_iso(),
        "type": event_type,
        "stage": stage,
        "status": status,
    }
    task_id = task.get("task_id")
    if task_id:
        item["event_id"] = f"EVT-{task_id}-{len(events) + 1:04d}"
    if actor:
        item["actor"] = actor
    if note:
        item["note"] = note
    events.append(item)


def bump_runtime(task, stage=None, status=None):
    runtime = task.setdefault("runtime", {})
    runtime["revision"] = int(runtime.get("revision", 0)) + 1
    runtime["updated_at"] = now_iso()
    if stage is not None:
        runtime["current_stage"] = stage
    if status is not None:
        runtime["status"] = status
