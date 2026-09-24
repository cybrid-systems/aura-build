def solve(s: str, k: int) -> int:
    n = len(s)
    if k <= 1:
        return n
    if k > n:
        return 0
    max_len = 0
    for target_unique in range(1, 27):
        freq = [0] * 26
        left = 0
        right = 0
        unique = 0
        count_at_least_k = 0
        while right < n:
            idx = ord(s[right]) - ord('a')
            if freq[idx] == 0:
                unique += 1
            freq[idx] += 1
            if freq[idx] == k:
                count_at_least_k += 1
            right += 1
            while unique > target_unique:
                idx_l = ord(s[left]) - ord('a')
                if freq[idx_l] == k:
                    count_at_least_k -= 1
                freq[idx_l] -= 1
                if freq[idx_l] == 0:
                    unique -= 1
                left += 1
            if unique == target_unique and unique == count_at_least_k:
                cur_len = right - left
                if cur_len > max_len:
                    max_len = cur_len
    return max_len


CASES = [
    {"s": "aaabb", "k": 3},
    {"s": "ababbc", "k": 2},
    {"s": "aabbcc", "k": 1},
    {"s": "abcdef", "k": 2},
    {"s": "a", "k": 1},
    {"s": "a", "k": 2},
    {"s": "aaabbb", "k": 3},
    {"s": "ababacb", "k": 3},
    {"s": "bbaa", "k": 3},
    {"s": "weitong", "k": 2},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(s=case["s"], k=case["k"])
        results.append({
            "id": i,
            "input": {"s": case["s"], "k": case["k"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
