#!/usr/bin/env python3
import sys

MAX_LINES = 600

errors = []
for path in sys.argv[1:]:
    with open(path) as f:
        count = sum(1 for _ in f)
    if count > MAX_LINES:
        errors.append(f"{path}: {count} lines (max {MAX_LINES})")

if errors:
    for e in errors:
        print(e, file=sys.stderr)
    sys.exit(1)
