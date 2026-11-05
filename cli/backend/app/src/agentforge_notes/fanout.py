"""Parallel fan-out group + join barrier (TASK-8).

A fan-out runs several development branches (each its own scripted run, in its own
run dir) concurrently and joins them under a ``completion_policy``:

- ``strict`` (default): every *required* branch must end ``succeeded`` or the join
  is blocked and handoff out of the development group is refused;
- ``best-effort``: a failed *optional* branch is flagged (``fanout_partial``) but
  the join still converges.

State lives in one manifest per fan-out,
``.notes/history/runs/<TASK_ID>/<GROUP_RUN_ID>/group-run.json`` — the ``pending_joins``-lite
model from the heavy concept. ``joined`` flips true once no branch is still
``pending``/``running``; ``ok`` reflects the policy verdict.

This module owns no shared-state writes: it builds manifests and incident records;
``commands.cmd_fanout`` (the single writer) appends incidents and registers
artifacts into ``task.json``.
"""
import json

from . import incidents
from .clock import now_iso
from .json_store import save_json
from .paths import ROOT, RUNS_DIR, group_run_dir

# Branch lifecycle on the manifest. running/pending block the join barrier; the
# rest are terminal run outcomes mirrored from execute_run's final_status.
BRANCH_PENDING = {"pending", "running"}
BRANCH_TERMINAL = {"succeeded", "failed", "blocked"}


def next_group_run_id(task_id):
    """Return the next monotonic ``GRP-<TASK_ID>-NNN`` without reusing a dir."""
    base = RUNS_DIR / task_id
    highest = 0
    if base.is_dir():
        prefix = f"GRP-{task_id}-"
        for child in base.iterdir():
            if child.is_dir() and child.name.startswith(prefix):
                tail = child.name[len(prefix):]
                if tail.isdigit():
                    highest = max(highest, int(tail))
    return f"GRP-{task_id}-{highest + 1:03d}"


def build_manifest(task_id, group_run_id, group, policy, branches):
    """branches: list of {stage_id, run_id, required}. Initial status=running."""
    return {
        "schema_version": 1,
        "group_run_id": group_run_id,
        "task_id": task_id,
        "group": group,
        "policy": policy,
        "branches": [
            {
                "stage_id": b["stage_id"],
                "run_id": b["run_id"],
                "required": bool(b["required"]),
                "status": "running",
            }
            for b in branches
        ],
        "joined": False,
        "ok": False,
        "created_at": now_iso(),
        "joined_at": None,
    }


def save_manifest(manifest):
    grp_dir = group_run_dir(manifest["task_id"], manifest["group_run_id"])
    grp_dir.mkdir(parents=True, exist_ok=True)
    save_json(grp_dir / "group-run.json", manifest)


def manifest_path(task_id, group_run_id):
    return group_run_dir(task_id, group_run_id) / "group-run.json"


def load_latest_group_run(task_id):
    """Return the most recent group-run manifest for a task, or None.

    Used by the advance-gate: a task may not leave the development group until its
    latest fan-out has ``joined`` and ``ok``."""
    base = RUNS_DIR / task_id
    if not base.is_dir():
        return None
    prefix = f"GRP-{task_id}-"
    latest = None
    latest_key = -1
    for child in base.iterdir():
        if child.is_dir() and child.name.startswith(prefix):
            tail = child.name[len(prefix):]
            if tail.isdigit() and int(tail) > latest_key:
                mpath = child / "group-run.json"
                if mpath.exists():
                    latest_key = int(tail)
                    latest = json.loads(mpath.read_text(encoding="utf-8"))
    return latest


def evaluate_join(manifest):
    """Apply the completion policy to terminal branch statuses.

    Returns ``(ok, incident_records)``. The caller (single writer) appends the
    incidents to the journal. Codes:

    - ``fanout_branch_failed`` — a required branch is not succeeded;
    - ``fanout_join_blocked`` — strict policy with ≥1 failed required branch;
    - ``fanout_partial`` — best-effort policy with ≥1 failed optional branch.
    """
    task_id = manifest["task_id"]
    policy = manifest.get("policy", "strict")
    branches = manifest.get("branches", [])

    failed_required = [b for b in branches
                       if b["required"] and b["status"] != "succeeded"]
    failed_optional = [b for b in branches
                       if not b["required"] and b["status"] != "succeeded"]

    recs = []
    manifest_link = str(manifest_path(task_id, manifest["group_run_id"]).relative_to(ROOT))

    def _inc(code, severity, message, next_action, branch=None):
        return incidents.make_incident(
            task_id, code, message, next_action, severity=severity,
            run_id=branch["run_id"] if branch else None,
            stage_id=branch["stage_id"] if branch else None,
            links=[manifest_link])

    for b in failed_required:
        recs.append(_inc(
            "fanout_branch_failed", "error",
            f"required branch {b['stage_id']} ended {b['status']}",
            "перезапустите ветку через harv retry " + b["run_id"], branch=b))

    if policy == "strict":
        ok = not failed_required
        if not ok:
            stages = ", ".join(b["stage_id"] for b in failed_required)
            recs.append(_inc(
                "fanout_join_blocked", "error",
                f"strict join blocked: required branches not succeeded: {stages}",
                "перезапустите упавшие ветки и повторите fanout/join"))
    else:  # best-effort
        ok = not failed_required  # required branches still gate the join
        for b in failed_optional:
            recs.append(_inc(
                "fanout_partial", "warning",
                f"optional branch {b['stage_id']} ended {b['status']} (best-effort)",
                "при необходимости перезапустите ветку через harv retry " + b["run_id"],
                branch=b))
        if failed_required:
            stages = ", ".join(b["stage_id"] for b in failed_required)
            recs.append(_inc(
                "fanout_join_blocked", "error",
                f"best-effort join blocked: required branches not succeeded: {stages}",
                "перезапустите обязательные ветки и повторите fanout/join"))

    return ok, recs
