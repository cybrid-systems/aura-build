def solve(t1, t2):
    def merge(a, b):
        if a is None and b is None:
            return None
        elif a is None:
            # clone b
            return (b[0], merge(None, b[1]), merge(None, b[2]))
        elif b is None:
            # clone a
            return (a[0], merge(a[1], None), merge(a[2], None))
        else:
            return (a[0] + b[0], merge(a[1], b[1]), merge(a[2], b[2]))
    return merge(t1, t2)

CASES = [
    {
        "t1": (1, (3, (5, None, None), (2, None, None)), None),
        "t2": (2, (1, None, (4, None, None)), (3, None, None)),
    },
    {
        "t1": None,
        "t2": None,
    },
    {
        "t1": (1, None, None),
        "t2": (2, (3, None, None), None),
    },
    {
        "t1": (1, (2, None, None), (3, None, None)),
        "t2": (4, (5, None, None), (6, None, None)),
    },
    {
        "t1": (1, (2, (4, None, None), None), (3, None, None)),
        "t2": (2, (1, None, (5, None, None)), (3, None, None)),
    },
    {
        "t1": (1, None, None),
        "t2": (2, (3, None, None), (4, None, None)),
    },
    {
        "t1": None,
        "t2": (1, (2, None, None), (3, None, None)),
    },
    {
        "t1": (1, (2, None, (4, None, None)), None),
        "t2": (1, None, (2, None, None)),
    },
]

if __name__ == '__main__':
    import json
    results = []
    for i, c in enumerate(CASES):
        result = solve(c["t1"], c["t2"])
        results.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False) if result is not None else "null"
        })
    print(json.dumps([{"id": r["id"], "input": r["input"], "expected": r["expected"]} for r in results], separators=(',', ':'), ensure_ascii=False))
