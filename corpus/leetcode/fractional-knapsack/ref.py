import json

def solve(n: int, W: int, items: list) -> float:
    # Sort items by value-to-weight ratio in non-increasing order.
    # Use float ratio for sorting key.
    sorted_items = sorted(items, key=lambda x: x[1] / x[0] if x[0] != 0 else 0.0, reverse=True)

    remaining = W
    total_value = 0.0

    for w, v in sorted_items:
        if remaining <= 0:
            break
        if w <= remaining:
            total_value += v
            remaining -= w
        else:
            # Take fraction
            total_value += v * (remaining / w)
            remaining = 0
            break

    return total_value


CASES = [
    {
        "id": 0,
        "input": {
            "n": 4,
            "W": 10,
            "items": [(5, 10), (4, 40), (6, 30), (3, 50)]
        }
    },
    {
        "id": 1,
        "input": {
            "n": 1,
            "W": 5,
            "items": [(10, 100)]
        }
    },
    {
        "id": 2,
        "input": {
            "n": 3,
            "W": 50,
            "items": [(10, 60), (20, 100), (30, 120)]
        }
    },
    {
        "id": 3,
        "input": {
            "n": 5,
            "W": 10,
            "items": [(2, 3), (3, 4), (4, 5), (5, 6), (1, 1)]
        }
    },
    {
        "id": 4,
        "input": {
            "n": 2,
            "W": 0,
            "items": [(1, 10), (2, 20)]
        }
    },
    {
        "id": 5,
        "input": {
            "n": 3,
            "W": 100,
            "items": [(100, 1), (100, 2), (100, 3)]
        }
    },
    {
        "id": 6,
        "input": {
            "n": 4,
            "W": 8,
            "items": [(3, 9), (4, 12), (5, 15), (2, 4)]
        }
    },
]


if __name__ == '__main__':
    results = []
    for case in CASES:
        inp = case["input"]
        result = solve(inp["n"], inp["W"], inp["items"])
        # Round to 6 decimals for canonical output (avoid floating noise)
        canonical = round(result, 6)
        results.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(canonical, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
