#!/usr/bin/env python3
"""Coerce Aura json-encode empty-list→null back to [] for known list fields."""
import re
import sys

FIELDS = (
    "discarded",
    "env_notes",
    "storm",
    "actions",
    "worldlines",
    "stable_refs",
    "updated_keys",
    "tips",
)

def main() -> None:
    s = sys.stdin.read()
    for f in FIELDS:
        s = re.sub(
            rf'"{re.escape(f)}"\s*:\s*null',
            f'"{f}":[]',
            s,
        )
    sys.stdout.write(s)

if __name__ == "__main__":
    main()
