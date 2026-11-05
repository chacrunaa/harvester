import json
import os
import tempfile

from .errors import die


def load_json(path):
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        die(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        die(f"invalid json: {path}: {exc}")


def save_json(path, data):
    """Atomic write: serialize to a temp file in the same dir, then os.replace.

    os.replace is atomic on POSIX, so a crash mid-write never leaves a partially
    written control file — readers see either the old or the new content.
    """
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
