import sys
import json

def parse_list_literal(s):
    s = s.strip()
    # handle empty list
    if s in ('()', '[]'):
        return []
    # strip surrounding parens or brackets
    if s.startswith('(') and s.endswith(')'):
        s = s[1:-1].strip()
    elif s.startswith('[') and s.endswith(']'):
        s = s[1:-1].strip()
    if not s:
        return []
    # split by comma or whitespace
    parts = []
    buf = ''
    for ch in s:
        if ch in (',', ' ', '\t'):
            if buf:
                parts.append(buf)
                buf = ''
        else:
            buf += ch
    if buf:
        parts.append(buf)
    return [int(p) for p in parts if p]

def min_candies(ratings):
    n = len(ratings)
    if n == 0:
        return 0
    if n == 1:
        return 1
    left = [1] * n
    right = [1] * n
    for i in range(1, n):
        if ratings[i] > ratings[i-1]:
            left[i] = left[i-1] + 1
    for i in range(n-2, -1, -1):
        if ratings[i] > ratings[i+1]:
            right[i] = right[i+1] + 1
    total = 0
    for i in range(n):
        total += max(left[i], right[i])
    return total

def solve(case_input):
    """
    case_input: list of ints (ratings)
    Returns: minimum total candies as int
    """
    return min_candies(case_input)

CASES = [
    {"id": 0, "input": [1, 0, 2]},
    {"id": 1, "input": [1, 2, 2, 4, 3]},
    {"id": 2, "input": [4, 3, 2, 1]},
    {"id": 3, "input": []},
    {"id": 4, "input": [5]},
    {"id": 5, "input": [1, 2, 3, 4, 5]},
    {"id": 6, "input": [5, 4, 3, 2, 1]},
    {"id": 7, "input": [1, 3, 4, 5, 2]},
]

def main():
    # parse stdin cases
    stdin_cases = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line.startswith('CASE'):
            eq_idx = line.find('=')
            if eq_idx == -1:
                continue
            payload = line[eq_idx+1:]
            parsed = parse_list_literal(payload)
            stdin_cases.append(parsed)

    if stdin_cases:
        results = []
        for ratings in stdin_cases:
            results.append(solve(ratings))
        for r in results:
            print(r)
        return

    # fallback: run predefined cases and print JSON array with computed expected
    output = []
    for case in CASES:
        inp = case["input"]
        result = solve(inp)
        output.append({
            "id": case["id"],
            "input": {"ratings": inp},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))

if __name__ == '__main__':
    main()
