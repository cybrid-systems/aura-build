import sys
import json

def solve(s):
    stack = []
    current_num = 0
    current_str = []
    for ch in s:
        if ch.isdigit():
            current_num = current_num * 10 + int(ch)
        elif ch == '[':
            stack.append((current_str, current_num))
            current_str = []
            current_num = 0
        elif ch == ']':
            prev_str, num = stack.pop()
            decoded = ''.join(current_str) * num
            current_str = prev_str + list(decoded)
        else:
            current_str.append(ch)
    return ''.join(current_str)

CASES = [
    {"s": "3[a]2[bc]"},
    {"s": "3[a2[c]]"},
    {"s": "2[abc]3[cd]ef"},
    {"s": "10[a]"},
    {"s": "abc"},
    {"s": "0[abc]"},
    {"s": "2[a]2[b]3[c]"},
    {"s": "3[z2[y]b]"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        s = case["s"]
        out = solve(s)
        results.append({"id": i, "input": case, "expected": out})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
