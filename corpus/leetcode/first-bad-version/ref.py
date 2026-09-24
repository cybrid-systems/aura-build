import json

def solve(n, is_bad_version):
    lo, hi = 1, n
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if is_bad_version(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


CASES = [
    {"id": 0, "args": {"n": 5, "bad": 4}},
    {"id": 1, "args": {"n": 1, "bad": 1}},
    {"id": 2, "args": {"n": 2126753390, "bad": 1702766719}},
    {"id": 3, "args": {"n": 2, "bad": 2}},
    {"id": 4, "args": {"n": 2, "bad": 1}},
    {"id": 5, "args": {"n": 100, "bad": 1}},
    {"id": 6, "args": {"n": 100, "bad": 100}},
    {"id": 7, "args": {"n": 2147483647, "bad": 2147483647}},
]


def _encode(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False)


if __name__ == '__main__':
    results = []
    for case in CASES:
        n = case["args"]["n"]
        bad = case["args"]["bad"]
        def is_bad_version(v, _bad=bad):
            return v >= _bad
        result = solve(n, is_bad_version)
        results.append({
            "id": case["id"],
            "input": _encode({"n": n, "bad": bad}),
            "expected": _encode(result),
        })
    print(_encode(results))
