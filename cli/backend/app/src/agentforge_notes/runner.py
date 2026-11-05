"""Sub-agent runner protocol (TASK-5).

Implements the scripted-orchestration contract from
``docs/architecture/scripted-orchestration.md``:

- ``build_run_request``   — RunRequestBuilder
- ``run_provider``        — ProviderAdapter (generic command adapter)
- ``next_run_id`` / ``run_dir`` helpers — RunStore
- ``validate_result`` / ``check_artifacts`` — ResultValidator
- ``make_incident`` / ``write_incidents`` — RunEventWriter (incident side)

The runner never edits ``tasks/backlog/**`` and never performs handoff; it only
produces request/result/raw artifacts and machine-readable incidents. Stage
transitions remain the job of ``harv move`` / handoff validation (TASK-6).
"""
import json
import os
import shlex
import subprocess
import time

from . import incidents
from .clock import now_iso
from .json_store import save_json
from .paths import ROOT, run_dir, runs_task_dir

# result.status is the agent-declared outcome (TASK-5). Run-level timed_out /
# cancelled live in metadata.json + an incident, not here (two-level model).
RESULT_STATUSES = {"succeeded", "failed", "needs_user_input", "blocked"}

REQUIRED_RESULT_FIELDS = [
    "schema_version", "run_id", "task_id", "stage_id", "status",
    "summary", "artifacts", "questions", "incidents", "next_action",
]

_UNSAFE_CHARS = {"/", "\\", "\x00"}


# --- path safety -----------------------------------------------------------

def is_path_safe(segment):
    """A path segment is safe if it is non-empty, not '.'/'..', and has no
    separators or NUL — required because run_id/task_id/stage_id become path
    segments under .notes/history/runs."""
    if not segment or segment in (".", ".."):
        return False
    return not (_UNSAFE_CHARS & set(segment))


# --- RunStore --------------------------------------------------------------

def next_run_id(task_id):
    """Return the next monotonic ``RUN-<TASK_ID>-NNN`` without reusing an
    existing run directory."""
    base = runs_task_dir(task_id)
    highest = 0
    if base.is_dir():
        prefix = f"RUN-{task_id}-"
        for child in base.iterdir():
            if child.is_dir() and child.name.startswith(prefix):
                tail = child.name[len(prefix):]
                if tail.isdigit():
                    highest = max(highest, int(tail))
    return f"RUN-{task_id}-{highest + 1:03d}"


# --- RunRequestBuilder -----------------------------------------------------

def build_run_request(task, stage_cfg, run_id, owner, provider, timeout,
                      previous_run_id=None):
    task_id = task["task_id"]
    subst = lambda items: [p.replace("<TASK_ID>", task_id) for p in items]
    request = {
        "schema_version": 1,
        "run_id": run_id,
        "task_id": task_id,
        "stage_id": stage_cfg["id"],
        "group": stage_cfg.get("group"),
        "role": stage_cfg.get("role"),
        "owner": owner,
        "target_root": str(ROOT.parent),
        "notes_root": str(ROOT),
        "inputs": subst(stage_cfg.get("required_inputs", [])),
        "expected_outputs": subst(stage_cfg.get("required_outputs_on_success", [])),
        "timeout_seconds": timeout,
        "provider": provider,
        "started_at": now_iso(),
    }
    if previous_run_id:
        request["previous_run_id"] = previous_run_id
    return request


# --- ProviderAdapter (generic command) -------------------------------------

def run_provider(request, rd, provider_cmd, timeout):
    """Run the external agent runner. Thin: passes the run directory through the
    environment, captures stdout/stderr/raw output, applies timeout. Returns a
    dict with exit_code, timed_out and duration_seconds."""
    request_path = rd / "request.json"
    result_path = rd / "result.json"
    argv = shlex.split(provider_cmd)
    env = dict(os.environ)
    env["HARV_RUN_REQUEST"] = str(request_path)
    env["HARV_RUN_RESULT"] = str(result_path)
    env["HARV_RUN_DIR"] = str(rd)
    env["HARV_NOTES_ROOT"] = request["notes_root"]

    timed_out = False
    exit_code = None
    started = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=request.get("target_root") or str(rd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        exit_code = proc.returncode
        stdout, stderr = proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _as_text(exc.stdout)
        stderr = _as_text(exc.stderr)
    duration = round(time.monotonic() - started, 3)

    (rd / "stdout.txt").write_text(stdout, encoding="utf-8")
    (rd / "stderr.txt").write_text(stderr, encoding="utf-8")
    (rd / "raw-output.txt").write_text(stdout + stderr, encoding="utf-8")
    return {
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_seconds": duration,
        "result_path": result_path,
    }


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value


# --- ResultValidator -------------------------------------------------------

def validate_result(result_path, request):
    """Return (result_dict_or_None, incidents). result is None when the
    structured contract is not satisfied — an exit code of 0 is never enough."""
    if not result_path.exists():
        return None, [make_incident(
            request, "invalid_structured_result", "critical",
            "provider did not produce result.json", "retry")]
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [make_incident(
            request, "invalid_structured_result", "critical",
            f"result.json is not valid JSON: {exc}", "retry")]
    missing = [f for f in REQUIRED_RESULT_FIELDS if f not in result]
    if missing:
        return None, [make_incident(
            request, "invalid_structured_result", "error",
            f"result.json missing fields: {', '.join(missing)}", "retry")]
    if result.get("status") not in RESULT_STATUSES:
        return None, [make_incident(
            request, "invalid_structured_result", "error",
            f"invalid result status: {result.get('status')!r}", "retry")]
    return result, []


def check_artifacts(result, request):
    """Cross-check declared artifacts and expected outputs against the
    filesystem. Detects missing outputs and artifacts created on disk but not
    declared in the result."""
    found = []
    notes = ROOT
    declared = [a.get("path") for a in result.get("artifacts", []) if a.get("path")]

    for path in declared:
        if not (notes / path).exists():
            found.append(make_incident(
                request, "required_output_missing", "error",
                f"declared artifact not found on disk: {path}", "hold"))

    for path in request.get("expected_outputs", []):
        exists = (notes / path).exists()
        if not exists:
            found.append(make_incident(
                request, "required_output_missing", "error",
                f"expected output missing: {path}", "hold"))
        elif path not in declared:
            found.append(make_incident(
                request, "partial_artifacts", "warning",
                f"output exists on disk but is not declared in result: {path}",
                "hold"))
    return found


# --- RunEventWriter (incidents) --------------------------------------------

def make_incident(request, code, severity, message, next_action):
    """Build a run incident in the canonical TASK-7 shape (incident_id assigned
    on append to the central journal)."""
    return incidents.make_incident(
        request["task_id"], code, message, next_action,
        severity=severity, run_id=request.get("run_id"),
        stage_id=request.get("stage_id"))


def write_incidents(task_id, items):
    """Append run incidents to the canonical journal (history/incidents.jsonl)."""
    return incidents.append_incidents(task_id, items)


def write_run_files(rd, request=None, result=None, metadata=None):
    if request is not None:
        save_json(rd / "request.json", request)
    if result is not None:
        save_json(rd / "result.json", result)
    if metadata is not None:
        save_json(rd / "metadata.json", metadata)
