import json
import sys

class Logger:
    def __init__(self):
        self._last_printed = {}

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:
        last = self._last_printed.get(message)
        if last is None or timestamp - last >= 10:
            self._last_printed[message] = timestamp
            return True
        return False


def _parse_operations(lines):
    """Parse operations file format into list of (op, args).
    INIT -> ('INIT', None)
    SHOULD_PRINT t "msg" -> ('SHOULD_PRINT', (t, msg))
    """
    ops = []
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if s == "INIT":
            ops.append(("INIT", None))
            continue
        if s.startswith("SHOULD_PRINT"):
            # tokenize manually
            parts = s.split(None, 2)
            ts = int(parts[1])
            # message may be quoted; strip quotes
            msg = parts[2]
            if len(msg) >= 2 and msg[0] == '"' and msg[-1] == '"':
                msg = msg[1:-1]
            ops.append(("SHOULD_PRINT", (ts, msg)))
            continue
    return ops


def solve(input_data):
    """input_data: list of strings (lines). Returns list of booleans for each SHOULD_PRINT."""
    ops = _parse_operations(input_data)
    results = []
    logger = None
    for op, args in ops:
        if op == "INIT":
            logger = Logger()
        elif op == "SHOULD_PRINT":
            ts, msg = args
            res = logger.shouldPrintMessage(ts, msg)
            results.append(res)
    return results


# ---------------- Test Cases ----------------
CASES = [
    # 0: classic example from prompt
    {
        "lines": [
            "INIT",
            'SHOULD_PRINT 1 "foo"',
            'SHOULD_PRINT 2 "bar"',
            'SHOULD_PRINT 3 "foo"',
            'SHOULD_PRINT 8 "foo"',
            'SHOULD_PRINT 10 "foo"',
            'SHOULD_PRINT 11 "foo"',
        ]
    },
    # 1: empty after init
    {
        "lines": ["INIT"]
    },
    # 2: unique messages all should print
    {
        "lines": [
            "INIT",
            'SHOULD_PRINT 0 "a"',
            'SHOULD_PRINT 5 "b"',
            'SHOULD_PRINT 9 "c"',
            'SHOULD_PRINT 20 "d"',
        ]
    },
    # 3: same message exactly 10s gap -> should print (>=10 rule)
    {
        "lines": [
            "INIT",
            'SHOULD_PRINT 0 "msg"',
            'SHOULD_PRINT 10 "msg"',
            'SHOULD_PRINT 20 "msg"',
        ]
    },
    # 4: identical message back-to-back same timestamp
    {
        "lines": [
            "INIT",
            'SHOULD_PRINT 100 "hi"',
            'SHOULD_PRINT 100 "hi"',
            'SHOULD_PRINT 100 "hi"',
            'SHOULD_PRINT 109 "hi"',
            'SHOULD_PRINT 110 "hi"',
        ]
    },
    # 5: multiple distinct messages interleaved with suprema
    {
        "lines": [
            "INIT",
            'SHOULD_PRINT 1 "x"',
            'SHOULD_PRINT 1 "y"',
            'SHOULD_PRINT 5 "x"',
            'SHOULD_PRINT 11 "y"',
            'SHOULD_PRINT 11 "x"',
        ]
    },
    # 6: very large timestamp gaps; messages with spaces & special chars
    {
        "lines": [
            "INIT",
            'SHOULD_PRINT 1 "hello world"',
            'SHOULD_PRINT 1000000000 "hello world"',
            'SHOULD_PRINT 1000000005 "hello world"',
            'SHOULD_PRINT 1000000015 "hello world"',
        ]
    },
    # 7: alternating between 2 messages, each gets ~printed every 11s
    {
        "lines": [
            "INIT",
            'SHOULD_PRINT 0 "alpha"',
            'SHOULD_PRINT 0 "beta"',
            'SHOULD_PRINT 10 "alpha"',
            'SHOULD_PRINT 10 "beta"',
            'SHOULD_PRINT 20 "alpha"',
            'SHOULD_PRINT 21 "beta"',
        ]
    },
]


def _to_jsonable(result):
    """Encode boolean results as True/False strings? Spec says json.dumps result.
    Use canonical bool -> True/False which is standard JSON."""
    return result


if __name__ == "__main__":
    out = []
    for i, case in enumerate(CASES):
        res = solve(case["lines"])
        # Make sure results are plain Python bools (json-friendly)
        res_canonical = [bool(x) for x in res]
        out.append({
            "id": i,
            "input": {"lines": case["lines"]},
            "expected": json.dumps(res_canonical, separators=(',', ':'), ensure_ascii=False),
        })
    sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
