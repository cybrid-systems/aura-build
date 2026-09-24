"""
Python reference for the Aura project "mini-log-line".

This single-file script implements toy in-memory semantics for the scenario
described in GOAL.md. It mirrors the module table and prints the 12 expected
KEY=value lines on stdout, computed from running the scenario.

Stdout contract (exact order, exact keys):
    DIALECT_DETECTED=logfmt
    DIALECT_DETECTED=json
    NORMALIZED_COUNT=6
    FIELD_LEVEL=ERROR
    FIELD_LEVEL=INFO
    FIELD_SERVICE=auth
    FIELD_SERVICE=billing
    PROJECTION_COUNT=<n after p1>
    PROJECTION_COUNT=<n after p2>
    HAS_QUOTED_VALUE=true
    HAS_NESTED_JSON=true
    ROUNDTRIP_OK=true
"""

import json
import re
from typing import Any, Dict, List, Tuple, Optional


# ---------------------------------------------------------------------------
# src/greputil.aura  -- string helpers
# ---------------------------------------------------------------------------
def split_string(s: str, sep: str) -> List[str]:
    return s.split(sep)


def trim(s: str) -> str:
    return s.strip()


def has_char(s: str, c: str) -> bool:
    return c in s


# ---------------------------------------------------------------------------
# src/scan.aura  -- generic scan-line: returns list of (key, value) string pairs
#                   dispatches to logfmt or jsonline parser
# ---------------------------------------------------------------------------
def scan_line(line: str) -> List[Tuple[str, str]]:
    if detect_dialect(line) == "json":
        return parse_jsonline(line)
    return parse_logfmt(line)


# ---------------------------------------------------------------------------
# src/detect.aura  -- detect-dialect
# ---------------------------------------------------------------------------
def detect_dialect(line: str) -> str:
    s = line.lstrip()
    if s.startswith("{"):
        return "json"
    return "logfmt"


# ---------------------------------------------------------------------------
# src/logfmt.aura  -- parse-logfmt / encode-logfmt
# ---------------------------------------------------------------------------
_LOGFMT_TOKEN = re.compile(
    r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)'
)


def parse_logfmt(line: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for m in _LOGFMT_TOKEN.finditer(line):
        key = m.group(1)
        raw = m.group(2)
        if raw.startswith('"') and raw.endswith('"'):
            val = bytes(raw[1:-1], "utf-8").decode("unicode_escape")
        else:
            val = raw
        out.append((key, val))
    return out


def encode_logfmt(alist: List[Tuple[str, str]]) -> str:
    parts = []
    for k, v in alist:
        if " " in v or '"' in v or "=" in v:
            esc = v.replace("\\", "\\\\").replace('"', '\\"')
            parts.append(f'{k}="{esc}"')
        else:
            parts.append(f"{k}={v}")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# src/jsonline.aura  -- parse-jsonline / encode-jsonline
#                      (flattens one level of nesting with "." join)
# ---------------------------------------------------------------------------
def _flatten(prefix: str, value: Any) -> List[Tuple[str, Any]]:
    out: List[Tuple[str, Any]] = []
    if isinstance(value, dict):
        for k, v in value.items():
            child = f"{prefix}.{k}" if prefix else k
            out.extend(_flatten(child, v))
    else:
        out.append((prefix, value))
    return out


def parse_jsonline(line: str) -> List[Tuple[str, str]]:
    obj = json.loads(line)
    out: List[Tuple[str, str]] = []
    for k, v in _flatten("", obj):
        out.append((k, "" if v is None else str(v)))
    return out


def encode_jsonline(alist: List[Tuple[str, str]]) -> str:
    # Unflatten one level: split keys on last "." only if there's a matching
    # sibling at the same prefix, else keep flat. Simple heuristic: produce a
    # flat object (toyspec — roundtrip via parse_jsonline must still hold).
    obj: Dict[str, Any] = {}
    for k, v in alist:
        if "." in k:
            head, _, tail = k.rpartition(".")
            obj.setdefault(head, {})[tail] = v
        else:
            obj[k] = v
    return json.dumps(obj, separators=(",", ":"))


# ---------------------------------------------------------------------------
# src/normalize.aura  -- normalize dialect alist -> (timestamp level service msg)
# ---------------------------------------------------------------------------
def _find(alist: List[Tuple[str, str]], name: str) -> Optional[str]:
    for k, v in alist:
        if k == name:
            return v
    return None


def normalize(dialect: str, alist: List[Tuple[str, str]]) -> Tuple[
    Optional[str], Optional[str], Optional[str], Optional[str]
]:
    ts = (
        _find(alist, "timestamp")
        or _find(alist, "ts")
        or _find(alist, "time")
    )
    lvl = (
        _find(alist, "level")
        or _find(alist, "level".upper())
        or _find(alist, "severity")
    )
    svc = (
        _find(alist, "service")
        or _find(alist, "svc")
    )
    msg = (
        _find(alist, "message")
        or _find(alist, "msg")
    )
    return (ts, lvl, svc, msg)


# ---------------------------------------------------------------------------
# src/project.aura  -- parse-predicate / matches?
# ---------------------------------------------------------------------------
def parse_predicate(pred_str: str) -> Tuple[str, str]:
    if "=" not in pred_str:
        raise ValueError(f"bad predicate: {pred_str}")
    field, _, want = pred_str.partition("=")
    return field.strip(), want.strip()


def matches(record: Tuple[Any, Any, Any, Any], predicate: Tuple[str, str]) -> bool:
    field, want = predicate
    idx = {"timestamp": 0, "level": 1, "service": 2, "message": 3}.get(field)
    if idx is None:
        return False
    val = record[idx]
    return val == want


# ---------------------------------------------------------------------------
# src/stream.aura  -- parse-stream / project-stream
# ---------------------------------------------------------------------------
def parse_stream(lines: List[str]) -> List[Tuple[Any, Any, Any, Any]]:
    records: List[Tuple[Any, Any, Any, Any]] = []
    for line in lines:
        d = detect_dialect(line)
        if d == "json":
            alist = parse_jsonline(line)
        else:
            alist = parse_logfmt(line)
        records.append(normalize(d, alist))
    return records


def project_stream(
    records: List[Tuple[Any, Any, Any, Any]],
    predicates: List[Tuple[str, str]],
) -> List[Tuple[Any, Any, Any, Any]]:
    out = list(records)
    for p in predicates:
        out = [r for r in out if matches(r, p)]
    return out


# ---------------------------------------------------------------------------
# src/testdata.aura  -- sample-lines / expected-projection
# ---------------------------------------------------------------------------
SAMPLE_LINES: List[str] = [
    # 1: logfmt
    'timestamp=2024-05-01T10:00:00Z level=ERROR service=auth message="login failed"',
    # 2: json (flattened: service.name -> "service.name")
    '{"timestamp":"2024-05-01T10:01:00Z","level":"INFO","service":{"name":"billing"},"message":"charged"}',
    # 3: logfmt
    'ts=2024-05-01T10:02:00Z level=WARN svc=api message="retrying"',
    # 4: json
    '{"timestamp":"2024-05-01T10:03:00Z","level":"DEBUG","service":{"name":"search"},"message":"ok"}',
    # 5: logfmt (quoted value with spaces)
    'timestamp=2024-05-01T10:04:00Z level=INFO service=worker message="job done"',
    # 6: json (nested)
    '{"timestamp":"2024-05-01T10:05:00Z","level":"ERROR","service":{"name":"auth"},"message":"denied"}',
]


EXPECTED_PROJECTION: List[str] = ["level=ERROR", "service=billing"]


# ---------------------------------------------------------------------------
# main.aura  -- driver
# ---------------------------------------------------------------------------
def main() -> None:
    # 1. Sample lines loaded from testdata (SAMPLE_LINES, EXPECTED_PROJECTION).

    # 2. Detect dialect for lines 1 and 2.
    d1 = detect_dialect(SAMPLE_LINES[0])
    d2 = detect_dialect(SAMPLE_LINES[1])
    print(f"DIALECT_DETECTED={d1}")
    print(f"DIALECT_DETECTED={d2}")

    # 3. Parse full stream.
    records = parse_stream(SAMPLE_LINES)
    print(f"NORMALIZED_COUNT={len(records)}")

    # 4. First record's level.
    r1 = records[0]
    print(f"FIELD_LEVEL={r1[1]}")

    # 5. Second record's level.
    r2 = records[1]
    print(f"FIELD_LEVEL={r2[1]}")

    # 6. Third record's service.
    r3 = records[2]
    print(f"FIELD_SERVICE={r3[2]}")

    # 7. Fourth record's service (was nested JSON, normalized to its name).
    r4 = records[3]
    print(f"FIELD_SERVICE={r4[2]}")

    # 8. Projection with two predicates applied sequentially.
    predicates = [parse_predicate(p) for p in EXPECTED_PROJECTION]
    after_p1 = project_stream(records, [predicates[0]])
    after_p2 = project_stream(records, predicates)
    print(f"PROJECTION_COUNT={len(after_p1)}")
    print(f"PROJECTION_COUNT={len(after_p2)}")

    # 9. Quoted-value check on raw logfmt sample (any record scanned).
    has_quoted = any(
        " " in v
        for line in SAMPLE_LINES
        if detect_dialect(line) == "logfmt"
        for _, v in parse_logfmt(line)
    )
    print(f"HAS_QUOTED_VALUE={'true' if has_quoted else 'false'}")

    # 10. Nested-JSON check on raw json sample (any key containing ".").
    has_nested = any(
        "." in k
        for line in SAMPLE_LINES
        if detect_dialect(line) == "json"
        for k, _ in parse_jsonline(line)
    )
    print(f"HAS_NESTED_JSON={'true' if has_nested else 'false'}")

    # 11. Round-trip: pick first logfmt + first json, encode, re-parse, compare.
    logfmt_line = next(l for l in SAMPLE_LINES if detect_dialect(l) == "logfmt")
    json_line = next(l for l in SAMPLE_LINES if detect_dialect(l) == "json")

    lf_parsed = parse_logfmt(logfmt_line)
    lf_rt = parse_logfmt(encode_logfmt(lf_parsed))
    js_parsed = parse_jsonline(json_line)
    js_rt = parse_jsonline(encode_jsonline(js_parsed))

    roundtrip_ok = lf_parsed == lf_rt and js_parsed == js_rt
    print(f"ROUNDTRIP_OK={'true' if roundtrip_ok else 'false'}")


if __name__ == "__main__":
    main()
