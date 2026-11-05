"""Incident journal + failure-code catalog (TASK-7).

One canonical journal — `.notes/history/incidents.jsonl` — is the source of
truth for "what broke and what to do next". Every failure path (runner,
handoff validation, lease conflicts) appends here. New incidents are appended;
status changes (resolve/acknowledge/ignore) rewrite the affected record.

Events (`task.json -> events`) answer "what happened"; incidents answer "what
broke". Raw logs stay in `runs/**` and are never mixed into this control state.
"""
import json

from .clock import now_iso
from .paths import HISTORY

INCIDENTS_JOURNAL = HISTORY / "incidents.jsonl"

SEVERITIES = {"info", "warning", "error", "critical"}
INCIDENT_STATUSES = {"open", "acknowledged", "resolved", "ignored"}

# Canonical failure codes (TASK-7). Catalog is minimal, not exhaustive — extra
# codes (e.g. partial_artifacts) are allowed but should be added here.
FAILURE_CODES = {
    "validation_failed",
    "required_input_missing",
    "required_output_missing",
    "artifact_missing",
    "schema_error",
    "queue_drift",
    "stale_revision",
    "lease_conflict",
    "stale_lease",
    "runner_failed",
    "runner_timeout",
    "invalid_structured_result",
    "tool_failed",
    "tool_denied",
    "io_error",
    "unexpected_exception",
    "partial_artifacts",
    # fan-out group join (TASK-8)
    "fanout_branch_failed",
    "fanout_join_blocked",
    "fanout_partial",
}


def make_incident(task_id, code, message, next_action, *, severity="error",
                  run_id=None, stage_id=None, links=None):
    """Build an incident record (incident_id assigned on append)."""
    return {
        "incident_id": None,
        "at": now_iso(),
        "task_id": task_id,
        "run_id": run_id,
        "stage_id": stage_id,
        "severity": severity,
        "code": code,
        "message": message,
        "next_action": next_action,
        "status": "open",
        "links": links or [],
    }


def _read_all():
    if not INCIDENTS_JOURNAL.exists():
        return []
    out = []
    for line in INCIDENTS_JOURNAL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _write_all(items):
    INCIDENTS_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)
    tmp = INCIDENTS_JOURNAL.with_name(INCIDENTS_JOURNAL.name + ".tmp")
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(INCIDENTS_JOURNAL)


def _next_seq(task_id, existing):
    prefix = f"INC-{task_id}-"
    highest = 0
    for item in existing:
        iid = item.get("incident_id") or ""
        if iid.startswith(prefix) and iid[len(prefix):].isdigit():
            highest = max(highest, int(iid[len(prefix):]))
    return highest


def append_incidents(task_id, incidents):
    """Append incidents to the journal, assigning stable INC-<TASK>-NNNN ids."""
    if not incidents:
        return incidents
    seq = _next_seq(task_id, _read_all())
    INCIDENTS_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with INCIDENTS_JOURNAL.open("a", encoding="utf-8") as fh:
        for inc in incidents:
            seq += 1
            inc["incident_id"] = f"INC-{task_id}-{seq:04d}"
            inc.setdefault("task_id", task_id)
            fh.write(json.dumps(inc, ensure_ascii=False) + "\n")
    return incidents


def load_incidents(task=None, status=None):
    items = _read_all()
    if task:
        items = [i for i in items if i.get("task_id") == task]
    if status:
        items = [i for i in items if i.get("status") == status]
    return items


def get_incident(incident_id):
    for item in _read_all():
        if item.get("incident_id") == incident_id:
            return item
    return None


def set_status(incident_id, status, note=None, actor=None):
    """Mutate one incident's status (resolve/acknowledge/ignore). Returns the
    updated record or None if not found."""
    items = _read_all()
    updated = None
    for item in items:
        if item.get("incident_id") == incident_id:
            item["status"] = status
            item["updated_at"] = now_iso()
            if note:
                item["resolution"] = note
            if actor:
                item["resolved_by"] = actor
            updated = item
            break
    if updated:
        _write_all(items)
    return updated
