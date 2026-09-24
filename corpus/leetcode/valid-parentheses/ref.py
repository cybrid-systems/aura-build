import json

def solve(s: str) -> bool:
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for ch in s:
        if ch in '([{':
            stack.append(ch)
        elif ch in ')]}':
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack

CASES = [
    {"s": "()"},
    {"s": "()[]{}"},
    {"s": "(]"},
    {"s": "([)]"},
    {"s": "{[]}"},
    {"s": ""},
    {"s": "["},
    {"s": "(())"},
    {"s": "(((())))"},
    {"s": "({[)]}"},
    {"s": "([{}])"},
    {"s": "}()"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
