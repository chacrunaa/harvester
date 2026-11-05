"""Unified command output contract.

Every command emits either a human-readable rendering (default) or a JSON
envelope (``--json``):

    success: {"ok": true,  "command": ..., "task_id": ..., "data": {...}}
    error:   {"ok": false, "command": ..., "task_id": ..., "error": {code, message, next_action}}

Write paths raise ``CommandError`` instead of calling ``die`` so the failure can
be rendered in the same contract with a machine-readable ``code`` and a
``next_action`` hint.
"""
import json
import sys


class CommandError(Exception):
    def __init__(self, code, message, next_action=None, task_id=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.next_action = next_action
        self.task_id = task_id


def respond(args, command, data=None, human=None, task_id=None):
    if getattr(args, "json", False):
        print(json.dumps(
            {"ok": True, "command": command, "task_id": task_id, "data": data or {}},
            ensure_ascii=False, indent=2,
        ))
    elif human is not None:
        print(human)


def emit_error(args, command, error, task_id=None):
    task_id = task_id or error.task_id
    if getattr(args, "json", False):
        print(json.dumps(
            {
                "ok": False,
                "command": command,
                "task_id": task_id,
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "next_action": error.next_action,
                },
            },
            ensure_ascii=False, indent=2,
        ))
    else:
        print(f"error: {error.message}", file=sys.stderr)
        if error.next_action:
            print(f"next: {error.next_action}", file=sys.stderr)
