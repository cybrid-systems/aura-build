def solve(s):
    chars = list(s)
    n = len(chars)
    i = 0
    while i < n:
        # Find the end of the current word
        j = i
        while j < n and chars[j] != ' ':
            j += 1
        # Reverse the word in place using two pointers
        left, right = i, j - 1
        while left < right:
            chars[left], chars[right] = chars[right], chars[left]
            left += 1
            right -= 1
        # Move to the next word (skip the space)
        i = j + 1
    return ''.join(chars)


CASES = [
    {"s": "abc def"},
    {"s": "the sky is blue"},
    {"s": "a"},
    {"s": "ab cd ef gh"},
    {"s": "hello world"},
    {"s": "x"},
    {"s": "racecar"},
    {"s": "a b c d e"},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        inp = case["s"]
        out = solve(inp)
        results.append({
            "id": idx,
            "input": {"s": inp},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
