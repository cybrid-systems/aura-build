def solve(s: str, t: str) -> bool:
    if len(s) != len(t):
        return False
    freq = [0] * 26
    for ch in s:
        freq[ord(ch) - ord('a')] += 1
    for ch in t:
        idx = ord(ch) - ord('a')
        freq[idx] -= 1
        if freq[idx] < 0:
            return False
    return all(f == 0 for f in freq)


CASES = [
    {"s": "listen", "t": "silent"},
    {"s": "hello", "t": "world"},
    {"s": "anagram", "t": "nagaram"},
    {"s": "rat", "t": "car"},
    {"s": "a", "t": "b"},
    {"s": "a", "t": "a"},
    {"s": "abc", "t": "abcd"},
    {"s": "abcdefghijklmnopqrstuvwxyz", "t": "zyxwvutsrqponmlkjihgfedcba"},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(s=case["s"], t=case["t"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
