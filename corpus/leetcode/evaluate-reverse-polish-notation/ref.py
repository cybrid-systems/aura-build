def solve(tokens: list[str]) -> int:
    stack = []
    ops = {'+', '-', '*', '/'}
    for t in tokens:
        if t in ops:
            b = stack.pop()
            a = stack.pop()
            if t == '+':
                stack.append(a + b)
            elif t == '-':
                stack.append(a - b)
            elif t == '*':
                stack.append(a * b)
            else:  # t == '/'
                # Truncated division toward zero
                if (a >= 0 and b >= 0) or (a < 0 and b < 0) or a == 0:
                    stack.append(a // b)
                else:
                    stack.append(-(abs(a) // abs(b)))
        else:
            stack.append(int(t))
    return stack[-1]


CASES = [
    {"tokens": ["3", "4", "+", "5", "*"]},
    {"tokens": ["15", "7", "1", "1", "+", "-", "/", "3", "*", "2", "1", "1", "+", "+", "-"]},
    {"tokens": ["2", "1", "+", "3", "*"]},
    {"tokens": ["4", "13", "5", "/", "+"]},
    {"tokens": ["10", "6", "-", "9", "3", "+", "11", "*", "+"]},
    {"tokens": ["0", "1", "/"]},
    {"tokens": ["1", "2", "+", "3", "4", "-", "*", "5", "+"]},
    {"tokens": ["-3", "-4", "+", "2", "*"]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
