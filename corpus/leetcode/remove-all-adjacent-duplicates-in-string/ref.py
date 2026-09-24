def solve(s: str) -> str:
    stack = []
    for ch in s:
        if stack and stack[-1] == ch:
            stack.pop()
        else:
            stack.append(ch)
    return ''.join(stack)


CASES = [
    {"s": "abbaca"},
    {"s": "azxxzy"},
    {"s": "a"},
    {"s": "aa"},
    {"s": "abba"},
    {"s": "abcddcba"},
    {"s": "mississippi"},
    {"s": ""},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
