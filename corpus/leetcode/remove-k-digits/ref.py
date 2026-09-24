def solve(num: str, k: int) -> str:
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    # If k remains, remove from the end
    if k:
        stack = stack[:-k] if k else stack
    result = ''.join(stack).lstrip('0')
    return result if result else '0'


CASES = [
    {"num": "1432219", "k": 3},
    {"num": "10200", "k": 1},
    {"num": "10", "k": 2},
    {"num": "112", "k": 1},
    {"num": "9", "k": 1},
    {"num": "100000", "k": 1},
    {"num": "1234567890", "k": 9},
    {"num": "10001", "k": 4},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["num"], c["k"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
