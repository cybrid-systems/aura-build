def solve(a: str, b: str) -> str:
    i, j = len(a) - 1, len(b) - 1
    carry = 0
    result = []
    while i >= 0 or j >= 0 or carry:
        total = carry
        if i >= 0:
            total += a[i] == '1'
            i -= 1
        if j >= 0:
            total += b[j] == '1'
            j -= 1
        result.append('1' if total % 2 else '0')
        carry = total // 2
    return ''.join(reversed(result))

CASES = [
    {"a": "11", "b": "1"},
    {"a": "1010", "b": "1011"},
    {"a": "0", "b": "0"},
    {"a": "0", "b": "1"},
    {"a": "1", "b": "0"},
    {"a": "", "b": ""},
    {"a": "", "b": "1"},
    {"a": "1", "b": ""},
    {"a": "1111", "b": "1111"},
    {"a": "101010101010", "b": "010101010101"},
]

if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["a"], case["b"])
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
