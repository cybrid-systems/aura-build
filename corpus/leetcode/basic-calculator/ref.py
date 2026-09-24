import json
import sys

def solve(s: str) -> int:
    stack = []
    num = 0
    sign = 1
    result = 0
    
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch == '+':
            result += sign * num
            num = 0
            sign = 1
        elif ch == '-':
            result += sign * num
            num = 0
            sign = -1
        elif ch == '(':
            # Push current result and sign onto stack
            stack.append(result)
            stack.append(sign)
            # Reset for the new subexpression
            result = 0
            sign = 1
        elif ch == ')':
            result += sign * num
            num = 0
            # Pop sign and previous result
            prev_sign = stack.pop()
            prev_result = stack.pop()
            result = prev_result + prev_sign * result
            sign = 1
        # spaces are ignored
    
    result += sign * num
    return result


CASES = [
    {"s": "1 + 1"},
    {"s": "(1+(4+5+2)-3)+(6+8)"},
    {"s": " 2-1 + 2"},
    {"s": "1"},
    {"s": "0"},
    {"s": "(1)"},
    {"s": "1-2-3"},
    {"s": "((1+2)+(3+4))"},
    {"s": "100 + 200 - 50"},
    {"s": "10 - (2 + 3) - (5 - 1)"},
    {"s": "-(3 + 4)"},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        inp = case["s"]
        out = solve(inp)
        results.append({
            "id": i,
            "input": {"s": inp},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
