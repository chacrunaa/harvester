import sys


def die(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)
