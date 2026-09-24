import os
import json


def generate_parentheses(n):
    """Generate all well-formed parenthesis combinations of length 2*n using backtracking."""
    result = []
    if n == 0:
        return [""]
    current = []
    def backtrack(open_count, close_count):
        if open_count == n and close_count == n:
            result.append(''.join(current))
            return
        if open_count < n:
            current.append('(')
            backtrack(open_count + 1, close_count)
            current.pop()
        if close_count < open_count:
            current.append(')')
            backtrack(open_count, close_count + 1)
            current.pop()
    backtrack(0, 0)
    return result


def solve(n):
    """Solve function matching the problem signature."""
    return generate_parentheses(n)


CASES = [
    {"n": 0},
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 6},
    {"n": 7},
]


if __name__ == '__main__':
    output = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        output.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(sorted(result), separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
