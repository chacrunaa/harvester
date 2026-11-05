from .clock import now_iso
from .errors import die
from .json_store import load_json, save_json
from .paths import BACKLOG, STAGES_JSON, TASKS_JSON, task_json_path


def load_tasks_index():
    return load_json(TASKS_JSON)


def save_tasks_index(data):
    data["updated_at"] = now_iso()
    save_json(TASKS_JSON, data)


def load_stages():
    data = load_json(STAGES_JSON)
    return {stage["id"]: stage for stage in data.get("stages", [])}, data


def stage_config(stage):
    stages, _ = load_stages()
    config = stages.get(stage)
    if config is None:
        die(f"unknown stage: {stage}")
    return config


FORWARD_STATUSES = {"ready_for_next_stage", "done"}


def find_transitions(config, target):
    """Return (name, transition) pairs of the stage that lead to ``target``."""
    return [
        (name, tr)
        for name, tr in config.get("transitions", {}).items()
        if tr.get("next_stage") == target
    ]


# Default set of groups executed as a parallel fan-out (TASK-8). A fan-out group
# keeps runtime.current_stage on its anchor (entry) stage while branches run in
# parallel, so its exit transition lives on the anchor, not on the last branch.
DEFAULT_FANOUT_GROUPS = ("dev",)


def fanout_groups(stage_data):
    """Groups run as a parallel fan-out, from stages.json (default: dev)."""
    return set(stage_data.get("fanout_groups") or DEFAULT_FANOUT_GROUPS)


def group_blocks(stages):
    """Ordered list of (group, [stage_ids]) contiguous blocks in pipeline order.

    ``stages`` is the ordered {id: config} mapping from :func:`load_stages`.
    A group that appears in more than one block is a misconfiguration that
    :func:`collect_findings` reports as ``group_not_contiguous``."""
    blocks = []
    for sid, cfg in stages.items():
        group = cfg.get("group")
        if blocks and blocks[-1][0] == group:
            blocks[-1][1].append(sid)
        else:
            blocks.append((group, [sid]))
    return blocks


def group_exit_target(stages, group):
    """Entry stage of the group block following ``group``'s block, or None.

    This is where a fan-out group hands off when it leaves the group: the first
    stage of the next group in pipeline order."""
    blocks = group_blocks(stages)
    for i, (g, _ids) in enumerate(blocks):
        if g == group:
            return blocks[i + 1][1][0] if i + 1 < len(blocks) else None
    return None


def required_outputs(config, task_id):
    """required_outputs_on_success with <TASK_ID> substituted."""
    return [p.replace("<TASK_ID>", task_id) for p in config.get("required_outputs_on_success", [])]


def required_inputs(config, task_id):
    return [p.replace("<TASK_ID>", task_id) for p in config.get("required_inputs", [])]


def stage_dir(stage):
    return BACKLOG / stage_config(stage).get("directory", stage)


def queue_path(stage):
    return stage_dir(stage) / "queue.json"


def load_task(task_id):
    return load_json(task_json_path(task_id))


def save_task(task_id, data):
    save_json(task_json_path(task_id), data)


def load_queue(stage):
    return load_json(queue_path(stage))


def save_queue(stage, data):
    data["updated_at"] = now_iso()
    save_json(queue_path(stage), data)


def queue_has(queue, task_id):
    return any(item.get("task_id") == task_id for item in queue.get("items", []))


def add_to_queue(stage, task_id, priority=100):
    queue = load_queue(stage)
    if not queue_has(queue, task_id):
        task_link = task_json_path(task_id).relative_to(queue_path(stage).parent, walk_up=True)
        queue.setdefault("items", []).append(
            {
                "task_id": task_id,
                "task_link": str(task_link),
                "priority": priority,
            }
        )
    save_queue(stage, queue)


def remove_from_queue(stage, task_id):
    if stage == "done":
        return
    queue = load_queue(stage)
    queue["items"] = [
        item for item in queue.get("items", []) if item.get("task_id") != task_id
    ]
    save_queue(stage, queue)


def ensure_task_known(task_id):
    index = load_tasks_index()
    if task_id not in index.get("tasks", {}):
        die(f"task is not listed in tasks.json: {task_id}")
    if not task_json_path(task_id).exists():
        die(f"task.json does not exist: {task_json_path(task_id)}")
    return index
