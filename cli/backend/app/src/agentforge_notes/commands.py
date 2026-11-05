import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from . import fanout as fanout_mod
from . import incidents as incidents_journal
from . import runner
from .clock import MSK, lease_window, now_iso
from .events import add_event, bump_runtime
from .json_store import save_json
from .output import CommandError, respond
from .paths import BACKLOG, ROOT, RUNS_DIR, TASKS_DIR, handoff_dir, run_dir, task_dir

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_PROVIDER_CMD = f"python3 {_REPO_ROOT / 'store' / 'examples' / 'providers' / 'claude_runner.py'}"
from .tasks import (
    FORWARD_STATUSES,
    add_to_queue,
    fanout_groups,
    find_transitions,
    group_blocks,
    group_exit_target,
    load_queue,
    load_stages,
    load_task,
    load_tasks_index,
    queue_has,
    remove_from_queue,
    required_inputs,
    required_outputs,
    save_task,
    save_tasks_index,
    stage_config,
)


ARTIFACT_KEYS = {
    "brief": "briefs",
    "specification": "specifications",
    "report": "reports",
    "memory": "memory",
    "chat": "chats",
    "question": "questions",
}


# --- shared helpers --------------------------------------------------------

def artifact_exists(path):
    """Existence check tolerant of the mixed path bases used across the runtime.

    Artifacts live under ROOT/history; stages.json required_inputs also reference
    backlog files (tasks.json, stages.json, <group>/...) relative to BACKLOG, and
    some outputs (documentations/...) sit at the project root (ROOT.parent).
    """
    p = Path(path)
    if p.is_absolute():
        return p.exists()
    return (ROOT / p).exists() or (BACKLOG / p).exists() or (ROOT.parent / p).exists()


def require_known(task_id):
    if not (task_dir(task_id) / "task.json").exists():
        raise CommandError(
            "unknown_task",
            f"task not found: {task_id}",
            "проверьте task_id или выполните harv list",
            task_id=task_id,
        )
    index = load_tasks_index()
    if task_id not in index.get("tasks", {}):
        raise CommandError(
            "unknown_task",
            f"task is not listed in tasks.json: {task_id}",
            "выполните harv sync-index",
            task_id=task_id,
        )


def sync_task_index_runtime(task_id, task):
    index = load_tasks_index()
    entry = index.setdefault("tasks", {}).setdefault(task_id, {"task_id": task_id})
    runtime = task.get("runtime", {})
    entry["current_stage"] = runtime.get("current_stage")
    entry["status"] = runtime.get("status")
    entry["revision"] = runtime.get("revision")
    entry["runtime_updated_at"] = runtime.get("updated_at")
    save_tasks_index(index)


def lease_is_expired(lease):
    if not lease or not lease.get("expires_at"):
        return False
    try:
        return datetime.fromisoformat(lease["expires_at"]) < datetime.now(MSK)
    except ValueError:
        return False


# --- read commands ---------------------------------------------------------

def cmd_status(args):
    require_known(args.task_id)
    task = load_task(args.task_id)
    runtime = task.get("runtime", {})
    data = {
        "task_id": args.task_id,
        "topic": task.get("topic"),
        "stage": runtime.get("current_stage"),
        "status": runtime.get("status"),
        "revision": runtime.get("revision"),
        "lease": runtime.get("lease"),
        "artifacts": task.get("artifacts", {}),
    }
    respond(args, "status", data=data, task_id=args.task_id,
            human=json.dumps(data, ensure_ascii=False, indent=2))


def cmd_list(args):
    stages, _ = load_stages()
    index = load_tasks_index()
    epic_of = {}
    for epic in index.get("epics", []):
        for tid in epic.get("tasks", []):
            epic_of[tid] = epic.get("epic_id")

    rows = []
    for task_id, meta in index.get("tasks", {}).items():
        stage = meta.get("current_stage")
        group = stages.get(stage, {}).get("group")
        epic = epic_of.get(task_id)
        if args.stage and stage != args.stage:
            continue
        if args.group and group != args.group:
            continue
        if args.status and meta.get("status") != args.status:
            continue
        if args.epic and epic != args.epic:
            continue
        rows.append({
            "task_id": task_id,
            "topic": meta.get("topic"),
            "stage": stage,
            "status": meta.get("status"),
            "group": group,
            "epic": epic,
        })

    rows.sort(key=lambda r: r["task_id"])
    human = "\n".join(f"{r['task_id']}  {r['stage'] or '-':<22} {r['status'] or '-':<20} {r['topic'] or ''}"
                      for r in rows) or "нет задач"
    respond(args, "list", data={"tasks": rows}, human=human)


def cmd_queues(args):
    stages, _ = load_stages()
    queues = []
    for stage_id, config in stages.items():
        if args.stage and stage_id != args.stage:
            continue
        if args.group and config.get("group") != args.group:
            continue
        queue = load_queue(stage_id)
        queues.append({
            "stage": stage_id,
            "group": config.get("group"),
            "role": config.get("role"),
            "items": queue.get("items", []),
        })
    lines = []
    for q in queues:
        ids = ", ".join(i.get("task_id") for i in q["items"]) or "—"
        lines.append(f"{q['stage']:<22} [{q['role']}] {ids}")
    respond(args, "queues", data={"queues": queues}, human="\n".join(lines) or "нет очередей")


def cmd_artifacts(args):
    require_known(args.task_id)
    task = load_task(args.task_id)
    result = {}
    lines = []
    for key, items in task.get("artifacts", {}).items():
        entries = []
        for item in items:
            path = item.get("path") if isinstance(item, dict) else item
            exists = bool(path) and "<TASK_ID>" not in path and artifact_exists(path)
            entries.append({"path": path, "exists": exists})
            lines.append(f"[{'ok ' if exists else 'MISS'}] {key}: {path}")
        result[key] = entries
    respond(args, "artifacts", data={"artifacts": result}, task_id=args.task_id,
            human="\n".join(lines) or "нет артефактов")


def cmd_events(args):
    require_known(args.task_id)
    task = load_task(args.task_id)
    events = task.get("events", [])
    human = "\n".join(f"{e.get('at')}  {e.get('type'):<18} {e.get('stage')}  {e.get('status')}"
                      for e in events) or "нет событий"
    respond(args, "events", data={"events": events}, task_id=args.task_id, human=human)


# --- write commands --------------------------------------------------------

def cmd_take(args):
    require_known(args.task_id)
    stages, stage_data = load_stages()
    if args.stage not in stages:
        raise CommandError("unknown_stage", f"unknown stage: {args.stage}",
                           "выберите стадию из stages.json", task_id=args.task_id)

    task = load_task(args.task_id)
    runtime = task.setdefault("runtime", {})
    current_stage = runtime.get("current_stage")
    if current_stage != args.stage:
        raise CommandError("wrong_stage", f"task is in stage {current_stage}, not {args.stage}",
                           f"возьмите задачу на стадии {current_stage}", task_id=args.task_id)

    queue = load_queue(args.stage)
    if not queue_has(queue, args.task_id):
        raise CommandError("not_in_queue", f"task is not in queue: {args.stage}/queue.json",
                           "проверьте очередь через harv queues", task_id=args.task_id)

    lease = runtime.get("lease")
    if lease and lease.get("owner") != args.owner and not lease_is_expired(lease):
        raise CommandError("lease_held", f"task is already leased by {lease.get('owner')}",
                           "дождитесь release или используйте harv release --force-stale при истечении",
                           task_id=args.task_id)

    ttl = int(args.ttl_minutes or stage_data.get("protocol", {}).get("lease_ttl_minutes", 120))
    acquired, expires = lease_window(ttl)
    runtime["lease"] = {
        "owner": args.owner,
        "agent": stages[args.stage].get("role"),
        "acquired_at": acquired.isoformat(),
        "expires_at": expires.isoformat(),
    }
    bump_runtime(task, status="in_progress")
    add_event(task, "task_taken", args.stage, runtime["status"], actor=args.owner)
    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)
    respond(args, "take", data={"stage": args.stage, "owner": args.owner, "lease": runtime["lease"]},
            task_id=args.task_id, human=f"taken {args.task_id} in {args.stage} by {args.owner}")


def cmd_release(args):
    require_known(args.task_id)
    task = load_task(args.task_id)
    runtime = task.setdefault("runtime", {})
    lease = runtime.get("lease")
    if lease is None:
        respond(args, "release", data={"released": False, "reason": "no_lease"},
                task_id=args.task_id, human=f"{args.task_id}: lease уже свободен")
        return

    expired = lease_is_expired(lease)
    if args.force_stale:
        if not expired:
            raise CommandError("lease_active",
                               f"lease активен до {lease.get('expires_at')}",
                               "снимите без --force-stale, если вы владелец", task_id=args.task_id)
    elif lease.get("owner") != args.owner and not expired:
        raise CommandError("lease_held",
                           f"lease принадлежит {lease.get('owner')}",
                           "используйте --force-stale после истечения lease", task_id=args.task_id)

    runtime["lease"] = None
    bump_runtime(task)
    add_event(task, "task_released", runtime.get("current_stage"), runtime.get("status"),
              note="force-stale" if args.force_stale else None, actor=args.owner)
    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)
    respond(args, "release", data={"released": True, "was_expired": expired},
            task_id=args.task_id, human=f"released {args.task_id}")


def cmd_move(args):
    require_known(args.task_id)
    stages, _ = load_stages()
    if args.to != "done" and args.to not in stages:
        raise CommandError("unknown_stage", f"unknown target stage: {args.to}",
                           "выберите стадию из stages.json", task_id=args.task_id)

    task = load_task(args.task_id)
    runtime = task.setdefault("runtime", {})
    from_stage = runtime.get("current_stage")
    if not from_stage:
        raise CommandError("empty_stage", "task runtime.current_stage is empty",
                           "восстановите задачу через harv repair", task_id=args.task_id)

    chosen = None
    if not args.force:
        config = stages.get(from_stage)
        if config is None:
            raise CommandError("unknown_stage", f"current stage unknown: {from_stage}",
                               "используйте --force для recovery", task_id=args.task_id)
        transitions = find_transitions(config, args.to)
        if not transitions:
            raise CommandError("transition_not_allowed",
                               f"нет перехода {from_stage} -> {args.to}",
                               "выберите допустимый --to или используйте --force", task_id=args.task_id)
        chosen = transitions[0][1]
        if chosen.get("next_status") in FORWARD_STATUSES:
            for out in required_outputs(config, args.task_id):
                if not artifact_exists(out):
                    raise CommandError("required_output_missing", f"Missing {out}",
                                       "создайте и зарегистрируйте обязательный артефакт, затем move",
                                       task_id=args.task_id)

    status = args.status or (chosen.get("next_status") if chosen else None) \
        or ("done" if args.to == "done" else "ready_for_next_stage")
    remove_from_queue(from_stage, args.task_id)
    if args.to != "done":
        add_to_queue(args.to, args.task_id, args.priority)
        target_dir = stage_config(args.to).get("directory", args.to)
        task.setdefault("backlog", {})["queue_link"] = f"../../../tasks/backlog/{target_dir}/queue.json"

    runtime["lease"] = None
    bump_runtime(task, stage=args.to, status=status)
    add_event(task, "task_moved", args.to, status, note=f"{from_stage} -> {args.to}", actor=args.owner)
    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)
    respond(args, "move", data={"from": from_stage, "to": args.to, "status": status},
            task_id=args.task_id, human=f"moved {args.task_id}: {from_stage} -> {args.to} ({status})")


# --- advance (validating handoff, TASK-6) ----------------------------------

# Output paths under these dirs are real artifacts and must be registered in
# task.json; runtime files like history/tasks/<id>/task.json are not.
_ARTIFACT_DIR_PREFIXES = tuple(f"history/{key}/" for key in
                               ("briefs", "specifications", "reports", "memory", "chats"))


def _is_registerable_artifact(path):
    return path.startswith(_ARTIFACT_DIR_PREFIXES)


def _registered_paths(task):
    """All artifact paths registered in task.artifacts[*] (strings or {path})."""
    paths = set()
    for items in task.get("artifacts", {}).values():
        for item in items:
            path = item.get("path") if isinstance(item, dict) else item
            if path:
                paths.add(path)
    return paths


def _next_event_id(task_id):
    base = handoff_dir(task_id)
    highest = 0
    if base.is_dir():
        prefix = f"EVT-{task_id}-"
        for child in base.glob(f"{prefix}*.json"):
            tail = child.stem[len(prefix):]
            if tail.isdigit():
                highest = max(highest, int(tail))
    return f"EVT-{task_id}-{highest + 1:03d}"


def _error(code, message, next_action, path=None):
    item = {"code": code, "message": message, "next_action": next_action}
    if path is not None:
        item["path"] = path
    return item


def build_handoff_report(task, to_stage, owner, expect_revision, stages, stage_data=None):
    """Collect ALL transition problems into a validation report (does not raise).

    Returns (report, chosen_transition_or_None, next_status_or_None).
    """
    task_id = task["task_id"]
    runtime = task.get("runtime", {})
    from_stage = runtime.get("current_stage")
    errors, warnings = [], []

    report = {
        "ok": False,
        "task_id": task_id,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "errors": errors,
        "warnings": warnings,
        "checked_outputs": [],
    }

    if not from_stage:
        errors.append(_error("empty_stage", "runtime.current_stage is empty",
                             "восстановите задачу через harv repair"))
        return report, None, None
    if to_stage != "done" and to_stage not in stages:
        errors.append(_error("unknown_stage", f"unknown target stage: {to_stage}",
                             "выберите стадию из stages.json"))

    config = stages.get(from_stage)
    if config is None:
        errors.append(_error("unknown_stage", f"current stage unknown: {from_stage}",
                             "используйте harv move --force для recovery"))
        return report, None, None

    # optimistic concurrency
    if expect_revision is not None and int(expect_revision) != int(runtime.get("revision", 0)):
        errors.append(_error("stale_revision",
                             f"expected revision {expect_revision}, got {runtime.get('revision')}",
                             "перечитайте task.json и повторите"))

    # lease guard
    lease = runtime.get("lease")
    if lease and lease.get("owner") != owner and not lease_is_expired(lease):
        errors.append(_error("lease_held", f"task is leased by {lease.get('owner')}",
                             "дождитесь освобождения lease или используйте того же owner"))

    # queue membership of the source stage
    if not queue_has(load_queue(from_stage), task_id):
        errors.append(_error("queue_drift", f"task is not in queue: {from_stage}",
                             "выполните harv repair --apply"))

    # transition allowed
    chosen = None
    next_status = None
    from_group = config.get("group")
    fanout_set = fanout_groups(stage_data or {})
    transitions = find_transitions(config, to_stage)
    if transitions:
        chosen = transitions[0][1]
        next_status = chosen.get("next_status")
    elif (from_group in fanout_set
          and to_stage == group_exit_target(stages, from_group)):
        # Fan-out auto-exit (TASK-8): a fan-out group keeps the task on its anchor
        # stage, so the group exit need not be declared as an explicit transition.
        # If the latest group-run converged (joined+ok) the engine synthesizes the
        # handoff to the next group's entry stage. The join-gate below re-checks it.
        group_run = fanout_mod.load_latest_group_run(task_id)
        if group_run and group_run.get("joined") and group_run.get("ok") \
                and group_run.get("group") == from_group:
            chosen = {"next_stage": to_stage, "next_status": "ready_for_next_stage",
                      "synthesized": "fanout_group_exit"}
            next_status = "ready_for_next_stage"
        else:
            errors.append(_error("transition_not_allowed",
                                 f"нет перехода {from_stage} -> {to_stage}",
                                 "запустите harv fanout и дождитесь join, затем advance"))
    else:
        errors.append(_error("transition_not_allowed", f"нет перехода {from_stage} -> {to_stage}",
                             "выберите допустимый --to из stages.json"))

    # required inputs of the current stage (non-blocking drift signal)
    for path in required_inputs(config, task_id):
        if not artifact_exists(path):
            warnings.append(_error("required_input_missing", f"missing input: {path}",
                                   "проверьте подготовку стадии", path=path))

    # required outputs only for forward/accepted transitions
    if next_status in FORWARD_STATUSES:
        registered = _registered_paths(task)
        for path in required_outputs(config, task_id):
            report["checked_outputs"].append(path)
            if not artifact_exists(path):
                errors.append(_error("required_output_missing", f"missing output file: {path}",
                                     "создайте обязательный артефакт", path=path))
            elif _is_registerable_artifact(path) and path not in registered:
                errors.append(_error("artifact_not_registered",
                                     f"output not registered in task.json: {path}",
                                     "выполните harv add-artifact", path=path))

    # fan-out join gate (TASK-8): leaving a fan-out group requires a converged
    # group-run under its completion policy.
    to_group = (stages.get(to_stage, {}) or {}).get("group")
    if (next_status in FORWARD_STATUSES and from_group in fanout_set
            and to_group != from_group):
        group_run = fanout_mod.load_latest_group_run(task_id)
        if not group_run or not group_run.get("joined"):
            errors.append(_error("fanout_join_blocked",
                                 "no converged fan-out: запустите harv fanout перед выходом из development",
                                 "выполните harv fanout и дождитесь join"))
        elif not group_run.get("ok"):
            errors.append(_error("fanout_join_blocked",
                                 f"fan-out {group_run.get('group_run_id')} join не сошёлся по политике {group_run.get('policy')}",
                                 "перезапустите упавшие ветки (harv retry) и повторите fanout"))

    report["ok"] = not errors
    return report, chosen, next_status


def cmd_advance(args):
    require_known(args.task_id)
    stages, stage_data = load_stages()
    task = load_task(args.task_id)
    runtime = task.setdefault("runtime", {})
    from_stage = runtime.get("current_stage")

    report, chosen, next_status = build_handoff_report(
        task, args.to, args.owner, args.expect_revision, stages, stage_data)

    event_id = _next_event_id(args.task_id)
    report["event_id"] = event_id
    report_path = handoff_dir(args.task_id) / f"{event_id}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(report_path, report)

    if not report["ok"]:
        # Durable incident: one handle pointing at the full validation report.
        codes = ", ".join(sorted({e["code"] for e in report["errors"]}))
        incidents_journal.append_incidents(args.task_id, [incidents_journal.make_incident(
            args.task_id, "validation_failed",
            f"handoff {from_stage} -> {args.to} blocked: {codes}",
            "разберите ошибки в validation report и повторите advance",
            severity="error", stage_id=from_stage,
            links=[str(report_path.relative_to(ROOT))])])
        # Surface the full problem list (report shape, not the standard envelope).
        if getattr(args, "json", False):
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"handoff blocked: {args.task_id} {from_stage} -> {args.to}", file=sys.stderr)
            for err in report["errors"]:
                print(f"  [{err['code']}] {err['message']} -> {err['next_action']}", file=sys.stderr)
        raise SystemExit(1)

    # Apply the transition as one control operation.
    status = args.status or next_status or ("done" if args.to == "done" else "ready_for_next_stage")
    remove_from_queue(from_stage, args.task_id)
    backlog = task.setdefault("backlog", {})
    if args.to != "done":
        add_to_queue(args.to, args.task_id, args.priority)
        target_dir = stage_config(args.to).get("directory", args.to)
        backlog["queue_link"] = f"../../../tasks/backlog/{target_dir}/queue.json"
    else:
        backlog["queue_link"] = None

    runtime["lease"] = None
    bump_runtime(task, stage=args.to, status=status)
    add_event(task, "task_moved", args.to, status, note=f"{from_stage} -> {args.to}", actor=args.owner)
    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)

    report["status"] = status
    respond(args, "advance", data=report, task_id=args.task_id,
            human=(f"advanced {args.task_id}: {from_stage} -> {args.to} ({status})\n"
                   f"report: {report_path.relative_to(ROOT)}"))


def _register_artifact(task, task_id, art_type, path, owner, question=None):
    """Append an artifact to task.artifacts[<key>] and log the event.

    Shared by ``cmd_add_artifact`` (manual) and ``cmd_run`` (auto-registration
    of declared artifacts on a successful run).
    """
    key = ARTIFACT_KEYS.get(art_type)
    if not key:
        raise CommandError("unknown_artifact_type", f"unknown artifact type: {art_type}",
                           "используйте один из: " + ", ".join(sorted(ARTIFACT_KEYS)), task_id=task_id)
    artifacts = task.setdefault("artifacts", {})
    artifacts.setdefault(key, [])
    if path not in artifacts[key]:
        artifacts[key].append(path)
    if art_type == "question" and question:
        _append_question(task, task_id, question, owner)
    bump_runtime(task)
    add_event(task, "artifact_added", task["runtime"].get("current_stage"),
              task["runtime"].get("status"), note=path, actor=owner)


def cmd_add_artifact(args):
    require_known(args.task_id)
    task = load_task(args.task_id)
    _register_artifact(task, args.task_id, args.type, args.path, args.owner,
                       question=args.question)
    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)
    respond(args, "add-artifact", data={"type": args.type, "path": args.path},
            task_id=args.task_id, human=f"added {args.type} artifact to {args.task_id}: {args.path}")


# --- questions -------------------------------------------------------------

def _next_question_id(task, task_id):
    n = len(task.get("questions", [])) + 1
    return f"Q-{task_id}-{n:03d}"


def _append_question(task, task_id, text, owner):
    question = {
        "id": _next_question_id(task, task_id),
        "status": "open",
        "created_at": now_iso(),
        "answered_at": None,
        "question": text,
        "answer": None,
        "actor": owner,
    }
    task.setdefault("questions", []).append(question)
    return question


def _find_question(task, qid):
    for q in task.get("questions", []):
        if q.get("id") == qid:
            return q
    raise CommandError("question_not_found", f"question not found: {qid}",
                       "проверьте id через harv questions list", task_id=task.get("task_id"))


def cmd_questions(args):
    require_known(args.task_id)
    sub = args.questions_command
    if sub == "list":
        task = load_task(args.task_id)
        questions = task.get("questions", [])
        human = "\n".join(f"{q['id']} [{q['status']}] {q['question']}" for q in questions) or "нет вопросов"
        respond(args, "questions", data={"questions": questions}, task_id=args.task_id, human=human)
        return

    task = load_task(args.task_id)
    runtime = task.get("runtime", {})
    if sub == "add":
        q = _append_question(task, args.task_id, args.question, args.owner)
        event_type, note = "question_added", q["id"]
        result = q
    elif sub == "answer":
        q = _find_question(task, args.id)
        q["answer"] = args.answer
        q["status"] = "answered"
        q["answered_at"] = now_iso()
        event_type, note, result = "question_answered", q["id"], q
    elif sub == "close":
        q = _find_question(task, args.id)
        q["status"] = "closed"
        event_type, note, result = "question_closed", q["id"], q
    else:  # pragma: no cover - argparse guards
        raise CommandError("unknown_subcommand", f"unknown questions command: {sub}", None, task_id=args.task_id)

    bump_runtime(task)
    add_event(task, event_type, runtime.get("current_stage"), runtime.get("status"),
              note=note, actor=args.owner)
    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)
    respond(args, "questions", data={"question": result}, task_id=args.task_id,
            human=f"{note}: {result['status']}")


# --- create / sync ---------------------------------------------------------

TASK_ID_PREFIX = "HARV-"
TASK_ID_WIDTH = 3


def next_task_number(index):
    numbers = []
    for task_id in index.get("tasks", {}):
        if task_id.startswith(TASK_ID_PREFIX):
            try:
                numbers.append(int(task_id.split("-", 1)[1]))
            except ValueError:
                pass
    return max(numbers or [0]) + 1


def format_task_id(number):
    return f"{TASK_ID_PREFIX}{number:0{TASK_ID_WIDTH}d}"


def cmd_create(args):
    index = load_tasks_index()
    task_id = args.task_id or format_task_id(next_task_number(index))
    if task_id in index.get("tasks", {}):
        raise CommandError("task_exists", f"task already exists: {task_id}",
                           "выберите другой --task-id", task_id=task_id)

    root = task_dir(task_id)
    root.mkdir(parents=True, exist_ok=False)
    (root / "source.txt").write_text(args.description.rstrip() + "\n", encoding="utf-8")

    task = {
        "schema_version": 1,
        "task_id": task_id,
        "topic": args.description,
        "source": {"path": "source.txt", "source_id_mismatch": False},
        "backlog": {
            "index_link": "../../../tasks/backlog/tasks.json",
            "stages_link": "../../../tasks/backlog/stages.json",
            "queue_link": "../../../tasks/backlog/plan/stages/intake/queue.json",
        },
        "runtime": {
            "current_stage": "intake",
            "status": "new",
            "revision": 1,
            "lease": None,
            "updated_at": now_iso(),
        },
        "artifacts": {
            "briefs": [], "specifications": [], "reports": [],
            "memory": [], "chats": [], "questions": [],
        },
        "questions": [],
        "events": [],
    }
    add_event(task, "task_created", "intake", "new", actor="product-owner")
    save_task(task_id, task)

    index.setdefault("tasks", {})[task_id] = {
        "task_id": task_id,
        "topic": args.description,
        "description": args.description,
        "history_dir": f"../../history/tasks/{task_id}",
        "task_link": f"../../history/tasks/{task_id}/task.json",
        "current_stage": "intake",
        "status": "new",
        "revision": task["runtime"]["revision"],
        "runtime_updated_at": task["runtime"]["updated_at"],
    }
    epic_id = args.epic or "unassigned"
    epics = index.setdefault("epics", [])
    epic = next((item for item in epics if item.get("epic_id") == epic_id), None)
    if epic is None:
        epic = {"epic_id": epic_id, "description": "", "tasks": []}
        epics.append(epic)
    if task_id not in epic.setdefault("tasks", []):
        epic["tasks"].append(task_id)
    save_tasks_index(index)
    add_to_queue("intake", task_id, 100)
    if not queue_has(load_queue("intake"), task_id):
        raise CommandError("enqueue_failed", f"failed to enqueue {task_id} into intake",
                           "запустите harv repair --apply", task_id=task_id)
    respond(args, "create", data={"task_id": task_id, "stage": "intake"},
            task_id=task_id, human=f"created {task_id} in intake")


def cmd_sync_index(args):
    index = load_tasks_index()
    tasks = index.setdefault("tasks", {})
    synced = 0

    for task_root in sorted(TASKS_DIR.iterdir()):
        if not task_root.is_dir():
            continue
        if not (task_root / "task.json").is_file():
            continue
        task_id = task_root.name
        task = load_task(task_id)
        runtime = task.get("runtime", {})
        entry = tasks.setdefault(task_id, {})
        entry["task_id"] = task_id
        entry.setdefault("topic", task.get("topic", task_id))
        if task.get("description"):
            entry.setdefault("description", task["description"])
        elif task.get("topic"):
            entry.setdefault("description", task["topic"])
        entry["history_dir"] = f"../../history/tasks/{task_id}"
        entry["task_link"] = f"../../history/tasks/{task_id}/task.json"
        entry["current_stage"] = runtime.get("current_stage")
        entry["status"] = runtime.get("status")
        entry["revision"] = runtime.get("revision")
        entry["runtime_updated_at"] = runtime.get("updated_at")
        synced += 1

    save_tasks_index(index)
    respond(args, "sync-index", data={"synced": synced}, human=f"synced {synced} task index entries")


# --- validate --------------------------------------------------------------

def collect_findings(only_task=None):
    """Return a list of findings: {code, level, message, next_action}."""
    findings = []

    def err(code, message, next_action=None):
        findings.append({"code": code, "level": "error", "message": message, "next_action": next_action})

    def warn(code, message, next_action=None):
        findings.append({"code": code, "level": "warning", "message": message, "next_action": next_action})

    stages, stage_data = load_stages()
    valid_stages = set(stages) | {"done"}
    status_catalog = set(stage_data.get("status_catalog", []))

    for stage_id, config in stages.items():
        directory = config.get("directory")
        if not directory:
            err("stage_no_directory", f"{stage_id}: missing directory")
            continue
        stage_root = BACKLOG / directory
        if not stage_root.is_dir():
            err("stage_dir_missing", f"{stage_id}: missing directory {directory}")
        instructions = config.get("instructions")
        if not instructions:
            err("stage_no_instructions", f"{stage_id}: missing instructions")
        elif not (BACKLOG / instructions).is_file():
            err("stage_instructions_missing", f"{stage_id}: broken instructions {instructions}")
        queue_file = stage_root / "queue.json"
        if not queue_file.is_file():
            err("queue_missing", f"{stage_id}: missing queue.json")
            continue
        queue = load_queue(stage_id)
        if queue.get("stage") != stage_id:
            err("queue_stage_mismatch", f"{stage_id}: queue stage mismatch: {queue.get('stage')}")
        if queue.get("role") != config.get("role"):
            err("queue_role_mismatch", f"{stage_id}: queue role mismatch: {queue.get('role')}")
        if not (stage_root / "experience.json").is_file():
            err("experience_missing", f"{stage_id}: missing experience.json")
        for name, transition in config.get("transitions", {}).items():
            if transition.get("next_stage") not in valid_stages:
                err("bad_next_stage", f"{stage_id}.{name}: bad next_stage {transition.get('next_stage')}")

    for group in sorted({stage.get("group") for stage in stages.values()}):
        for path in (f"{group}/README.md", f"{group}/instructions.md",
                     f"{group}/queue.json", f"{group}/experience.json"):
            if not (BACKLOG / path).exists():
                err("group_file_missing", f"{group}: missing {path}")

    # Fan-out auto-exit safeguards (TASK-8): the engine derives a group's exit
    # from pipeline order, so groups must be contiguous blocks and every fan-out
    # group must be followed by another group to hand off to.
    blocks = group_blocks(stages)
    seen_groups = set()
    for group, _ids in blocks:
        if group in seen_groups:
            err("group_not_contiguous",
                f"{group}: group stages are not contiguous in stages.json",
                "переупорядочьте стадии так, чтобы стадии группы шли подряд")
        seen_groups.add(group)
    for group in fanout_groups(stage_data):
        if group not in seen_groups:
            continue
        if group_exit_target(stages, group) is None:
            err("fanout_group_no_exit",
                f"{group}: fan-out group has no following group to exit into",
                "добавьте стадию следующей группы после fan-out-группы")

    queued_by_task = {}
    for stage_id, config in stages.items():
        queue = load_queue(stage_id)
        queue_root = BACKLOG / config["directory"]
        for item in queue.get("items", []):
            task_id = item.get("task_id")
            queued_by_task.setdefault(task_id, []).append(stage_id)
            link = item.get("task_link")
            if link and not (queue_root / link).resolve().exists():
                err("broken_task_link", f"{stage_id}:{task_id}: broken task_link {link}")

    index = load_tasks_index()
    known_tasks = set(index.get("tasks", {}))
    for task_id, stages_with_task in queued_by_task.items():
        if task_id not in known_tasks:
            err("orphan_queue_item", f"{task_id}: orphan queue item in {stages_with_task}, not in tasks.json",
                "удалите запись через harv repair --apply")

    for task_id, meta in index.get("tasks", {}).items():
        if only_task and task_id != only_task:
            continue
        for key in ("history_dir", "task_link"):
            path = meta.get(key)
            if not path or not (BACKLOG / path).resolve().exists():
                err("broken_index_entry", f"{task_id}: broken tasks.json {key}: {path}")

        task = load_task(task_id)
        runtime = task.get("runtime", {})
        current_stage = runtime.get("current_stage")
        if current_stage not in valid_stages:
            err("invalid_current_stage", f"{task_id}: invalid current_stage {current_stage}")
            continue

        status = runtime.get("status")
        if status_catalog and status not in status_catalog:
            err("status_not_in_catalog", f"{task_id}: status {status} not in status_catalog")

        revision = runtime.get("revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            err("bad_revision", f"{task_id}: revision must be a positive integer, got {revision!r}")

        source_path = task.get("source", {}).get("path")
        if not source_path:
            err("missing_source_path", f"{task_id}: missing source.path")
        elif not (task_dir(task_id) / source_path).exists():
            err("source_file_missing", f"{task_id}: source file missing: {source_path}")

        lease = runtime.get("lease")
        if lease is not None:
            missing = [k for k in ("owner", "agent", "acquired_at", "expires_at") if not lease.get(k)]
            if missing:
                err("lease_bad_shape", f"{task_id}: lease missing fields {missing}")
            elif lease_is_expired(lease):
                warn("stale_lease", f"{task_id}: lease expired at {lease['expires_at']}",
                     "harv release --force-stale " + task_id)

        for e in task.get("events", []):
            if not all(e.get(k) for k in ("at", "type")):
                err("bad_event_shape", f"{task_id}: event missing at/type: {e}")
                break

        for meta_key, runtime_key in (
            ("current_stage", "current_stage"), ("status", "status"),
            ("revision", "revision"), ("runtime_updated_at", "updated_at"),
        ):
            if meta.get(meta_key) != runtime.get(runtime_key):
                err("index_drift",
                    f"{task_id}: tasks.json {meta_key} {meta.get(meta_key)} != task.json runtime.{runtime_key} {runtime.get(runtime_key)}",
                    "harv sync-index")

        if current_stage == "done":
            if task_id in queued_by_task:
                err("done_still_queued", f"{task_id}: done but still queued in {queued_by_task[task_id]}")
        else:
            queued_stages = queued_by_task.get(task_id, [])
            if queued_stages != [current_stage]:
                err("queue_drift", f"{task_id}: queued in {queued_stages}, current_stage is {current_stage}",
                    "harv repair --apply")
            expected_queue = f"../../../tasks/backlog/{stages[current_stage]['directory']}/queue.json"
            if task.get("backlog", {}).get("queue_link") != expected_queue:
                err("queue_link_drift",
                    f"{task_id}: queue_link {task.get('backlog', {}).get('queue_link')} != {expected_queue}",
                    "harv repair --apply")
            for inp in required_inputs(stages[current_stage], task_id):
                if not artifact_exists(inp):
                    warn("required_input_missing", f"{task_id}: required input missing: {inp}")

        registered = set()
        for items in task.get("artifacts", {}).values():
            for item in items:
                p = item.get("path") if isinstance(item, dict) else item
                if not p or "<TASK_ID>" in p:
                    continue
                registered.add((ROOT / p).resolve())
                if p.startswith("history/") and not (ROOT / Path(p)).exists():
                    warn("artifact_missing", f"{task_id}: missing artifact {p}")
                if p.startswith("harvester/") and not Path(p).exists():
                    warn("artifact_missing", f"{task_id}: missing artifact {p}")
        for found in (ROOT / "history").rglob(f"{task_id}.*"):
            if found.is_file() and found.suffix == ".md" and found.resolve() not in registered:
                warn("unregistered_artifact", f"{task_id}: unregistered artifact {found.relative_to(ROOT)}")

    return findings


def cmd_validate(args):
    findings = collect_findings(only_task=getattr(args, "task", None))
    errors = [f for f in findings if f["level"] == "error"]
    warnings = [f for f in findings if f["level"] == "warning"]
    ok = not errors

    respond(args, "validate", data={"ok": ok, "findings": findings},
            human=None if getattr(args, "json", False) else None)

    if not getattr(args, "json", False):
        if ok:
            print("validation ok")
        else:
            print("validation failed")
        for f in errors:
            print(f"ERROR: {f['message']}")
        for f in warnings:
            print(f"WARN: {f['message']}")

    if not ok:
        raise SystemExit(1)


# --- repair ----------------------------------------------------------------

def cmd_repair(args):
    stages, _ = load_stages()
    index = load_tasks_index()
    known_tasks = set(index.get("tasks", {}))

    queued_by_task = {}
    for stage_id, config in stages.items():
        for item in load_queue(stage_id).get("items", []):
            queued_by_task.setdefault(item.get("task_id"), []).append(stage_id)

    actions = []  # {action, task_id, detail, fn}

    # orphan queue items -> remove
    for task_id, in_stages in queued_by_task.items():
        if task_id not in known_tasks:
            for stage_id in in_stages:
                actions.append({
                    "action": "remove_orphan_queue_item", "task_id": task_id,
                    "detail": f"{stage_id}", "fn": (lambda s=stage_id, t=task_id: remove_from_queue(s, t)),
                })

    for task_id in known_tasks:
        task = load_task(task_id)
        runtime = task.get("runtime", {})
        stage = runtime.get("current_stage")
        if stage not in stages:
            continue  # repair can't pick a stage
        in_stages = queued_by_task.get(task_id, [])

        # missing queue item -> add (current_stage unambiguous)
        if in_stages != [stage]:
            for extra in in_stages:
                if extra != stage:
                    actions.append({
                        "action": "remove_wrong_queue_item", "task_id": task_id, "detail": extra,
                        "fn": (lambda s=extra, t=task_id: remove_from_queue(s, t)),
                    })
            if stage not in in_stages:
                actions.append({
                    "action": "add_missing_queue_item", "task_id": task_id, "detail": stage,
                    "fn": (lambda s=stage, t=task_id: add_to_queue(s, t, 100)),
                })

        # queue_link sync
        expected = f"../../../tasks/backlog/{stages[stage]['directory']}/queue.json"
        if task.get("backlog", {}).get("queue_link") != expected:
            def fix_link(t=task_id, exp=expected):
                tk = load_task(t)
                tk.setdefault("backlog", {})["queue_link"] = exp
                save_task(t, tk)
            actions.append({"action": "sync_queue_link", "task_id": task_id, "detail": expected, "fn": fix_link})

        # stale lease release
        lease = runtime.get("lease")
        if lease is not None and lease_is_expired(lease):
            def release_stale(t=task_id):
                tk = load_task(t)
                tk["runtime"]["lease"] = None
                bump_runtime(tk)
                add_event(tk, "task_released", tk["runtime"].get("current_stage"),
                          tk["runtime"].get("status"), note="repair stale lease", actor="repair")
                save_task(t, tk)
                sync_task_index_runtime(t, tk)
            actions.append({"action": "release_stale_lease", "task_id": task_id,
                            "detail": lease.get("expires_at"), "fn": release_stale})

    plan = [{"action": a["action"], "task_id": a["task_id"], "detail": a["detail"]} for a in actions]

    if args.apply:
        for a in actions:
            a["fn"]()
        human = "\n".join(f"applied {p['action']} {p['task_id']} ({p['detail']})" for p in plan) \
            or "нечего исправлять"
    else:
        human = "\n".join(f"would {p['action']} {p['task_id']} ({p['detail']})" for p in plan) \
            or "нечего исправлять (dry-run)"

    respond(args, "repair", data={"applied": bool(args.apply), "actions": plan}, human=human)


# --- run (sub-agent runner, TASK-5) ----------------------------------------

def execute_run(task, config, run_id, owner, provider, provider_cmd, timeout,
                previous_run_id=None):
    """Core of a single scripted run (TASK-5) WITHOUT touching shared control
    state.

    Creates the run directory, runs the provider, validates result/artifacts and
    persists request/result/metadata into that run dir only. Incidents are
    RETURNED (not appended to the central journal) and ``task.json`` is NOT
    modified — the caller decides when/whether to register artifacts and append
    incidents. This is what makes parallel fan-out safe: N branches can run this
    concurrently, each writing only its own run dir, while the join-command stays
    the single writer of ``task.json`` + ``incidents.jsonl`` (TASK-8).

    Returns ``{run_id, stage_id, status, result, incidents}``.
    """
    task_id = task["task_id"]
    stage_id = config["id"]
    rd = run_dir(task_id, run_id)
    rd.mkdir(parents=True, exist_ok=False)  # never reuse an existing run dir

    request = runner.build_run_request(
        task, config, run_id, owner, provider, timeout,
        previous_run_id=previous_run_id)
    runner.write_run_files(rd, request=request)

    started_at = now_iso()
    outcome = runner.run_provider(request, rd, provider_cmd, timeout)
    finished_at = now_iso()

    run_incidents = []  # timeout / invalid_result -> retry-able failure
    artifact_incidents = []  # missing / undeclared outputs -> manual decision (blocked)
    if outcome["timed_out"]:
        run_incidents.append(runner.make_incident(
            request, "runner_timeout", "error",
            f"provider exceeded timeout of {timeout}s", "retry"))

    result, validation_incidents = runner.validate_result(
        outcome["result_path"], request)
    run_incidents.extend(validation_incidents)

    if result is not None and result.get("status") == "succeeded":
        artifact_incidents.extend(runner.check_artifacts(result, request))

    incidents = run_incidents + artifact_incidents
    if outcome["timed_out"] or result is None or run_incidents:
        final_status = "failed"  # not trustworthy, safe to retry with a new run
    elif artifact_incidents:
        final_status = "blocked"  # declared/disk artifacts disagree -> manual call
    else:
        final_status = result.get("status")

    # Persist a machine-readable result record even when the provider failed.
    if result is None:
        result = {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": task_id,
            "stage_id": stage_id,
            "status": "failed",
            "summary": "run failed: no valid structured result",
            "artifacts": [],
            "questions": [],
            "incidents": [],
            "next_action": "retry",
        }
    result["status"] = final_status
    result["incidents"] = incidents
    if final_status == "failed":
        result["next_action"] = "retry"
    elif final_status == "blocked":
        result["next_action"] = "hold"

    runner.write_run_files(rd, result=result, metadata={
        "schema_version": 1,
        "run_id": run_id,
        "task_id": task_id,
        "provider": provider,
        "attempt": 1,
        "previous_run_id": previous_run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": outcome["duration_seconds"],
        "exit_code": outcome["exit_code"],
        "timed_out": outcome["timed_out"],
    })

    return {
        "run_id": run_id,
        "stage_id": stage_id,
        "status": final_status,
        "result": result,
        "incidents": incidents,
    }


def cmd_run(args):
    require_known(args.task_id)
    task = load_task(args.task_id)
    runtime = task.get("runtime", {})
    stage_id = args.stage or runtime.get("current_stage")
    config = stage_config(stage_id)
    owner = args.owner

    provider_cmd = args.provider_cmd or os.environ.get("HARV_PROVIDER_CMD") or _DEFAULT_PROVIDER_CMD

    # Validate path-safe id segments before they become directory names.
    for segment in (args.task_id, stage_id):
        if not runner.is_path_safe(segment):
            raise CommandError("unsafe_path", f"unsafe id segment: {segment!r}",
                               "id не должен содержать '.', '..', '/', '\\', NUL",
                               task_id=args.task_id)

    run_id = runner.next_run_id(args.task_id)
    add_event(task, "run_started", stage_id, runtime.get("status"), actor=owner,
              note=run_id)

    outcome = execute_run(task, config, run_id, owner, args.provider,
                          provider_cmd, args.timeout, previous_run_id=args.retry_of)
    final_status = outcome["status"]
    result = outcome["result"]
    incidents = outcome["incidents"]

    # cmd_run is the single writer here: append incidents + register artifacts.
    runner.write_incidents(args.task_id, incidents)

    if final_status == "succeeded":
        for art in result.get("artifacts", []):
            if art.get("type") and art.get("path"):
                _register_artifact(task, args.task_id, art["type"], art["path"], owner)
        add_event(task, "run_succeeded", stage_id, runtime.get("status"),
                  actor=owner, note=run_id)
    else:
        bump_runtime(task)
        add_event(task, "run_failed", stage_id, runtime.get("status"),
                  actor=owner, note=run_id)

    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)

    result_rel = str(run_dir(args.task_id, run_id).relative_to(ROOT))
    data = {
        "run_id": run_id,
        "status": final_status,
        "result_path": result_rel + "/result.json",
        "next_action": result.get("next_action"),
        "incidents": incidents,
    }

    if final_status != "succeeded":
        code = incidents[0]["code"] if incidents else "run_failed"
        if final_status == "blocked":
            hint = "разрешите incidents вручную (declared/disk artifacts расходятся)"
        else:
            hint = "проверьте incidents и повторите: harv run %s --retry-of %s" % (args.task_id, run_id)
        raise CommandError(code, f"run {run_id} {final_status}: {result.get('summary')}",
                           hint, task_id=args.task_id)

    respond(args, "run", data=data, task_id=args.task_id,
            human=("run %s succeeded\nartifacts registered: %d\nnext: harv move %s "
                   "(handoff validation)" % (run_id, len(result.get("artifacts", [])), args.task_id)))


# --- fanout (parallel development group + join, TASK-8) --------------------

def _parse_branch_cmds(entries):
    """Parse repeated ``--branch-cmd STAGE_ID=CMD`` into {stage_id: cmd}."""
    out = {}
    for entry in entries or []:
        if "=" not in entry:
            raise CommandError("bad_branch_cmd", f"invalid --branch-cmd: {entry!r}",
                               "формат: STAGE_ID=команда")
        stage_id, cmd = entry.split("=", 1)
        out[stage_id.strip()] = cmd.strip()
    return out


def cmd_fanout(args):
    require_known(args.task_id)
    stages, _ = load_stages()
    task = load_task(args.task_id)
    runtime = task.get("runtime", {})
    owner = args.owner

    # Group is inferred from the current stage (fallback to the development group).
    current_stage = runtime.get("current_stage")
    group = (stages.get(current_stage, {}) or {}).get("group") or "dev"

    # Branch list: explicit --branch wins, else every stage of the group.
    if args.branches:
        branch_ids = list(args.branches)
    else:
        branch_ids = sorted(sid for sid, cfg in stages.items()
                            if cfg.get("group") == group)
    if not branch_ids:
        raise CommandError("no_branches", f"no branches for group {group}",
                           "передайте --branch <stage_id>", task_id=args.task_id)

    optional = set(args.optional or [])
    default_cmd = args.provider_cmd or os.environ.get("HARV_PROVIDER_CMD") or _DEFAULT_PROVIDER_CMD
    branch_cmds = _parse_branch_cmds(args.branch_cmd)

    # Validate every branch: known stage, path-safe id, has a provider command.
    if not runner.is_path_safe(args.task_id):
        raise CommandError("unsafe_path", f"unsafe id segment: {args.task_id!r}",
                           "id не должен содержать '.', '..', '/', '\\', NUL",
                           task_id=args.task_id)
    branches = []
    for stage_id in branch_ids:
        if stage_id not in stages:
            raise CommandError("unknown_stage", f"unknown branch stage: {stage_id}",
                               "выберите стадию из stages.json", task_id=args.task_id)
        if not runner.is_path_safe(stage_id):
            raise CommandError("unsafe_path", f"unsafe id segment: {stage_id!r}",
                               "id не должен содержать '.', '..', '/', '\\', NUL",
                               task_id=args.task_id)
        cmd = branch_cmds.get(stage_id, default_cmd)
        if not cmd:
            raise CommandError("no_provider", f"no provider command for branch {stage_id}",
                               "передайте --provider-cmd или --branch-cmd STAGE=CMD",
                               task_id=args.task_id)
        branches.append({"stage_id": stage_id, "config": stages[stage_id],
                         "required": stage_id not in optional, "cmd": cmd})

    # Pre-allocate sequential run_ids in the main thread so concurrent branches
    # never collide on runner.next_run_id (which scans the dir).
    base_id = runner.next_run_id(args.task_id)
    prefix = f"RUN-{args.task_id}-"
    start = int(base_id[len(prefix):])
    for i, branch in enumerate(branches):
        branch["run_id"] = f"{prefix}{start + i:03d}"

    group_run_id = fanout_mod.next_group_run_id(args.task_id)
    manifest = fanout_mod.build_manifest(
        args.task_id, group_run_id, group, args.policy,
        [{"stage_id": b["stage_id"], "run_id": b["run_id"], "required": b["required"]}
         for b in branches])
    fanout_mod.save_manifest(manifest)

    add_event(task, "fanout_started", current_stage, runtime.get("status"),
              actor=owner, note=group_run_id)
    save_task(args.task_id, task)

    # Parallel spawn: each branch runs execute_run in its own thread, writing only
    # to its own run dir and RETURNING its outcome — no shared-state writes here.
    def _run_branch(branch):
        return execute_run(task, branch["config"], branch["run_id"], owner,
                           args.provider, branch["cmd"], args.timeout)

    outcomes = {}
    with ThreadPoolExecutor(max_workers=len(branches)) as pool:
        futures = {pool.submit(_run_branch, b): b for b in branches}
        for fut, b in futures.items():
            outcomes[b["stage_id"]] = (b, fut.result())

    # --- join (single writer) ----------------------------------------------
    status_by_stage = {sid: oc["status"] for sid, (b, oc) in outcomes.items()}
    for branch in manifest["branches"]:
        branch["status"] = status_by_stage.get(branch["stage_id"], "failed")

    ok, join_incidents = fanout_mod.evaluate_join(manifest)

    # Append all per-branch incidents + join incidents serially (no journal race).
    all_incidents = []
    for sid, (b, oc) in outcomes.items():
        all_incidents.extend(oc["incidents"])
    all_incidents.extend(join_incidents)
    incidents_journal.append_incidents(args.task_id, all_incidents)

    # Register artifacts of succeeded branches into the shared task.json.
    for sid, (b, oc) in outcomes.items():
        if oc["status"] == "succeeded":
            for art in oc["result"].get("artifacts", []):
                if art.get("type") and art.get("path"):
                    _register_artifact(task, args.task_id, art["type"], art["path"], owner)
            add_event(task, "run_succeeded", sid, runtime.get("status"),
                      actor=owner, note=oc["run_id"])
        else:
            add_event(task, "run_failed", sid, runtime.get("status"),
                      actor=owner, note=oc["run_id"])

    manifest["joined"] = True
    manifest["ok"] = ok
    manifest["joined_at"] = now_iso()
    fanout_mod.save_manifest(manifest)

    add_event(task, "fanout_joined" if ok else "fanout_blocked", current_stage,
              runtime.get("status"), actor=owner, note=f"{group_run_id}:{args.policy}")
    bump_runtime(task)
    save_task(args.task_id, task)
    sync_task_index_runtime(args.task_id, task)

    data = {
        "group_run_id": group_run_id,
        "policy": args.policy,
        "ok": ok,
        "joined": True,
        "branches": [
            {"stage_id": b["stage_id"], "run_id": b["run_id"],
             "required": b["required"], "status": status_by_stage.get(b["stage_id"])}
            for b in branches
        ],
        "incidents": all_incidents,
    }

    if not ok:
        failed = ", ".join(b["stage_id"] for b in branches
                           if b["required"] and status_by_stage.get(b["stage_id"]) != "succeeded")
        raise CommandError(
            "fanout_join_blocked",
            f"fanout {group_run_id} blocked ({args.policy}): required branches not succeeded: {failed}",
            "перезапустите упавшие ветки: harv retry <RUN_ID>, затем повторите fanout",
            task_id=args.task_id)

    human_lines = [f"fanout {group_run_id} joined ({args.policy}): ok"]
    for b in branches:
        st = status_by_stage.get(b["stage_id"])
        tag = "required" if b["required"] else "optional"
        human_lines.append(f"  {b['stage_id']:<24} [{tag}] {b['run_id']} -> {st}")
    human_lines.append(f"next: harv advance {args.task_id} --to test")
    respond(args, "fanout", data=data, task_id=args.task_id, human="\n".join(human_lines))


# --- incidents visibility + recovery (TASK-7) ------------------------------

def cmd_incidents(args):
    sub = getattr(args, "incidents_command", None)
    if sub == "show":
        inc = incidents_journal.get_incident(args.incident_id)
        if inc is None:
            raise CommandError("unknown_incident", f"incident not found: {args.incident_id}",
                               "проверьте id через harv incidents list")
        respond(args, "incidents", data=inc, task_id=inc.get("task_id"),
                human=json.dumps(inc, ensure_ascii=False, indent=2))
        return
    if sub == "resolve":
        status = args.status or "resolved"
        if status not in incidents_journal.INCIDENT_STATUSES:
            raise CommandError("bad_status", f"unknown status: {status}",
                               "используйте: " + ", ".join(sorted(incidents_journal.INCIDENT_STATUSES)))
        inc = incidents_journal.set_status(args.incident_id, status, note=args.note, actor=args.owner)
        if inc is None:
            raise CommandError("unknown_incident", f"incident not found: {args.incident_id}",
                               "проверьте id через harv incidents list")
        task_id = inc.get("task_id")
        if task_id and (task_dir(task_id) / "task.json").exists():
            task = load_task(task_id)
            add_event(task, "incident_resolved", task["runtime"].get("current_stage"),
                      task["runtime"].get("status"), note=f"{args.incident_id}:{status}", actor=args.owner)
            bump_runtime(task)
            save_task(task_id, task)
            sync_task_index_runtime(task_id, task)
        respond(args, "incidents", data=inc, task_id=task_id,
                human=f"{args.incident_id} -> {status}")
        return
    # default: list
    items = incidents_journal.load_incidents(task=args.task, status=args.status)
    human = "\n".join(
        f"{i['incident_id']}  [{i['severity']}/{i['status']}] {i['code']}: {i['message']}  -> {i['next_action']}"
        for i in items) or "нет инцидентов"
    respond(args, "incidents", data={"incidents": items}, human=human)


def cmd_retry(args):
    """Re-run a failed run with a fresh run_id, linking previous_run_id."""
    from types import SimpleNamespace
    matches = list(RUNS_DIR.glob(f"*/{args.run_id}/request.json"))
    if not matches:
        raise CommandError("unknown_run", f"run not found: {args.run_id}",
                           "проверьте run_id в .notes/history/runs")
    request = json.loads(matches[0].read_text(encoding="utf-8"))
    ns = SimpleNamespace(
        task_id=request["task_id"],
        stage=request.get("stage_id"),
        owner=request.get("owner", "manual"),
        provider=request.get("provider", "command"),
        provider_cmd=args.provider_cmd,
        timeout=args.timeout if args.timeout is not None else request.get("timeout_seconds", 3600),
        retry_of=args.run_id,
        json=getattr(args, "json", False),
    )
    cmd_run(ns)
