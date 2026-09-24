def solve(s, k):
    freq = [0] * 26
    left = 0
    max_freq = 0
    best = 0
    for right, ch in enumerate(s):
        idx = ord(ch) - 65
        freq[idx] += 1
        if freq[idx] > max_freq:
            max_freq = freq[idx]
        window_len = right - left + 1
        if window_len - max_freq > k:
            freq[ord(s[left]) - 65] -= 1
            left += 1
            window_len -= 1
        if window_len > best:
            best = window_len
    return best


CASES = [
    {"s": "ABAB", "k": 2},
    {"s": "AABABBA", "k": 1},
    {"s": "AAAA", "k": 0},
    {"s": "ABCDE", "k": 0},
    {"s": "ABCDE", "k": 2},
    {"s": "A", "k": 0},
    {"s": "ABBB", "k": 0},
    {"s": "ABBB", "k": 1},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["s"], case["k"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
