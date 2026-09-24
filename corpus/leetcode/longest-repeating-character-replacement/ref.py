def solve(s: str, k: int) -> int:
    if not s:
        return 0
    counts = {}
    max_freq = 0
    left = 0
    result = 0
    for right, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        if counts[ch] > max_freq:
            max_freq = counts[ch]
        window_len = right - left + 1
        if window_len - max_freq > k:
            counts[s[left]] -= 1
            left += 1
        else:
            if window_len > result:
                result = window_len
    return result


CASES = [
    {"s": "AABABBA", "k": 1},
    {"s": "", "k": 0},
    {"s": "AAAA", "k": 0},
    {"s": "ABCDE", "k": 0},
    {"s": "ABCDE", "k": 4},
    {"s": "AABABBA", "k": 2},
    {"s": "ABAA", "k": 0},
    {"s": "ABBB", "k": 2},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["s"], c["k"])
        out.append({
            "id": i,
            "input": {"s": c["s"], "k": c["k"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
