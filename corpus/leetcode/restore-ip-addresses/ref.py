def solve(s: str) -> list[str]:
    result = []
    n = len(s)
    if n < 4 or n > 12:
        return result

    def backtrack(start: int, parts: list[str], count: int):
        if count == 4:
            if start == n:
                result.append('.'.join(parts))
            return
        remaining = n - start
        needed = 4 - count
        if remaining < needed or remaining > needed * 3:
            return
        for length in (1, 2, 3):
            if start + length > n:
                break
            segment = s[start:start + length]
            if length > 1 and segment[0] == '0':
                continue
            value = int(segment)
            if value > 255:
                continue
            parts.append(segment)
            backtrack(start + length, parts, count + 1)
            parts.pop()

    backtrack(0, [], 0)
    return result


CASES = [
    {"id": 0, "s": "25525511135"},
    {"id": 1, "s": "00000"},
    {"id": 2, "s": "101023"},
    {"id": 3, "s": "0000"},
    {"id": 4, "s": "1111"},
    {"id": 5, "s": "010010"},
    {"id": 6, "s": "256256256256"},
    {"id": 7, "s": "12345"},
]


if __name__ == '__main__':
    import json

    out = []
    for case in CASES:
        s = case["s"]
        res = solve(s)
        out.append({
            "id": case["id"],
            "input": {"s": s},
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
