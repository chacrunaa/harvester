#!/usr/bin/env python3
"""Claude Code CLI provider adapter for harv fan-out branches.

Each branch in ``harv fanout`` is executed by a provider subprocess.
This adapter reads the harv run contract, builds a prompt from the stage
context, invokes ``claude --print`` as a subprocess, checks that expected
output files were created, and writes result.json.

Usage:
    HARV_PROVIDER_CMD="python store/examples/providers/claude_runner.py"
    harv fanout <TASK_ID> \\
        --branch backend --branch frontend --branch integration
"""
import json
import os
import subprocess
import sys
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────────

def _artifact_type(rel: str) -> str:
    name = rel.lower()
    if "brief" in name:
        return "brief"
    if "spec" in name:
        return "specification"
    if "memory" in name:
        return "memory"
    if "report" in name:
        return "report"
    if "chat" in name:
        return "chat"
    return "report"


def build_prompt(request: dict, notes_root: Path) -> str:
    task_id = request["task_id"]
    stage_id = request["stage_id"]
    role = request.get("role") or stage_id
    inputs = request.get("inputs", [])
    expected = request.get("expected_outputs", [])

    parts = [
        f"You are a {role} working on task {task_id}, stage {stage_id}.",
        "",
        "## Input context",
        "",
    ]

    for rel in inputs:
        path = notes_root / rel
        if path.exists():
            content = path.read_text(encoding="utf-8")
            parts += [f"### {rel}", "", content, ""]
        else:
            parts += [f"### {rel}", "", "(file not found — skip if not required)", ""]

    parts += [
        "## Your task",
        "",
        "Create ONLY the following output files. Write nothing else — do not",
        "create, modify, or delete any files outside these paths:",
        "",
    ]
    for rel in expected:
        parts.append(f"- {notes_root / rel}")

    parts += [
        "",
        "Rules:",
        "- Write each file completely with real content appropriate for the stage.",
        "- Do NOT modify the application source code or any files outside the paths listed above.",
        "- Do NOT create any files in .claude/, rules/, or any directory not listed above.",
        "- Do not ask questions. Do not skip any expected output file.",
        "- Base your output on the input context provided above.",
    ]

    return "\n".join(parts)


def run_claude(prompt: str, notes_root: Path, target_root: str, timeout: int) -> tuple[int, str, str]:
    """Run `claude --print` and return (exit_code, stdout, stderr)."""
    cmd = [
        "claude",
        "--print",
        "--add-dir", str(notes_root),
    ]
    if target_root and Path(target_root).is_dir():
        cmd += ["--add-dir", target_root]
    # Pass prompt via stdin: --add-dir takes <directories...> (variadic) and
    # would consume a positional prompt argument as a directory path.

    try:
        proc = subprocess.run(
            cmd,
            input=prompt,
            cwd=target_root or str(notes_root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"claude --print exceeded timeout of {timeout}s"
    except FileNotFoundError:
        return -1, "", "claude executable not found — ensure Claude Code CLI is installed"


def collect_artifacts(expected: list[str], notes_root: Path) -> tuple[list[dict], list[str]]:
    """Return (artifacts_present, missing_rels)."""
    artifacts = []
    missing = []
    for rel in expected:
        path = notes_root / rel
        if path.exists() and path.stat().st_size > 0:
            artifacts.append({
                "type": _artifact_type(rel),
                "path": rel,
                "description": f"created by claude_runner for stage {rel.split('/')[0] if '/' in rel else rel}",
            })
        else:
            missing.append(rel)
    return artifacts, missing


def write_result(result_path: Path, result: dict) -> None:
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    request_path = Path(os.environ["HARV_RUN_REQUEST"])
    result_path = Path(os.environ["HARV_RUN_RESULT"])
    notes_root = Path(os.environ["HARV_NOTES_ROOT"])

    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except Exception as exc:
        # Can't even read the contract — nothing to return except a best-effort result.
        fallback = {
            "schema_version": 1,
            "run_id": "unknown",
            "task_id": "unknown",
            "stage_id": "unknown",
            "status": "failed",
            "summary": f"claude_runner: failed to read request.json: {exc}",
            "artifacts": [],
            "questions": [],
            "incidents": [{"code": "provider_error", "message": str(exc)}],
            "next_action": "hold",
        }
        write_result(result_path, fallback)
        return 1

    run_id = request["run_id"]
    task_id = request["task_id"]
    stage_id = request["stage_id"]
    target_root = request.get("target_root", "")
    timeout = int(request.get("timeout_seconds", 300))
    expected = request.get("expected_outputs", [])

    prompt = build_prompt(request, notes_root)
    exit_code, stdout, stderr = run_claude(prompt, notes_root, target_root, timeout)

    # Log raw output to run dir for debugging.
    run_dir = Path(os.environ.get("HARV_RUN_DIR", result_path.parent))
    (run_dir / "claude-stdout.txt").write_text(stdout, encoding="utf-8")
    (run_dir / "claude-stderr.txt").write_text(stderr, encoding="utf-8")

    artifacts, missing = collect_artifacts(expected, notes_root)

    if exit_code == 0 and not missing:
        result = {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": task_id,
            "stage_id": stage_id,
            "status": "succeeded",
            "summary": f"claude_runner: stage {stage_id} completed, {len(artifacts)} artifact(s) created",
            "artifacts": artifacts,
            "questions": [],
            "incidents": [],
            "next_action": "advance",
        }
    else:
        incidents = []
        if exit_code != 0:
            incidents.append({
                "code": "provider_nonzero_exit",
                "message": f"claude exited with code {exit_code}",
                "detail": stderr[:2000] if stderr else "",
            })
        for rel in missing:
            incidents.append({
                "code": "missing_output",
                "message": f"expected output not created: {rel}",
            })
        result = {
            "schema_version": 1,
            "run_id": run_id,
            "task_id": task_id,
            "stage_id": stage_id,
            "status": "failed",
            "summary": (
                f"claude_runner: stage {stage_id} failed — "
                f"exit={exit_code}, missing={len(missing)} output(s)"
            ),
            "artifacts": artifacts,
            "questions": [],
            "incidents": incidents,
            "next_action": "retry",
        }

    write_result(result_path, result)
    return 0 if result["status"] == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main())
