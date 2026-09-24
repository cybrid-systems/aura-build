def solve(digits):
    if not digits:
        return []
    mapping = {
        '2': 'abc', '3': 'def', '4': 'ghi',
        '5': 'jkl', '6': 'mno', '7': 'pqrs',
        '8': 'tuv', '9': 'wxyz'
    }
    result = ['']
    for d in digits:
        letters = mapping[d]
        new_result = []
        for prefix in result:
            for ch in letters:
                new_result.append(prefix + ch)
        result = new_result
    return result


CASES = [
    {"digits": ""},
    {"digits": "2"},
    {"digits": "7"},
    {"digits": "23"},
    {"digits": "234"},
    {"digits": "79"},
    {"digits": "237"},
    {"digits": "9"},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(**c)
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
