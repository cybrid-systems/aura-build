import sys
import json


def solve(temps):
    n = len(temps)
    res = [0] * n
    stack = []  # stack of indices with decreasing temps
    for i in range(n):
        while stack and temps[stack[-1]] < temps[i]:
            idx = stack.pop()
            res[idx] = i - idx
        stack.append(i)
    return res


CASES = [
    {"temps": [73, 74, 75, 71, 69, 72, 76, 73]},
    {"temps": [30, 40, 50, 60]},
    {"temps": [30, 60, 90]},
    {"temps": [90, 60, 30]},
    {"temps": [70]},
    {"temps": []},
    {"temps": [0, -1, -2, -3, -4]},
    {"temps": [-5, -5, -5, -5, -5]},
]


def _parse_input(data):
    line = data.strip().splitlines()[0] if data.strip() else ""
    if "=" in line:
        _, payload = line.split("=", 1)
    else:
        payload = line
    return json.loads(payload)


if __name__ == "__main__":
    results = []
    # Case 0: read from stdin
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        if data.strip():
            temps_in = _parse_input(data)
            out = solve(temps_in)
            sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
            sys.exit(0)
    # CASES harness
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    sys.stdout.write(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
