import json

def solve(s: list) -> None:
    """Reverse the list in-place using two-pointer swap."""
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1


CASES = [
    {"s": ["s", "e", "t", "o", "f"]},
    {"s": ["h", "e", "l", "l", "o"]},
    {"s": ["a"]},
    {"s": ["a", "b"]},
    {"s": ["a", "b", "c"]},
    {"s": ["a", "b", "c", "d", "e", "f"]},
    {"s": ["z", "y", "x", "w"]},
    {"s": ["m", "n", "o", "p", "q", "r", "s", "t"]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        s = list(case["s"])
        solve(s)
        expected = json.dumps(s, separators=(',', ':'), ensure_ascii=False)
        results.append({
            "id": i,
            "input": {"s": case["s"]},
            "expected": expected,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
