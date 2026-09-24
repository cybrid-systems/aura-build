def remove_duplicates(s, k):
    stack = []  # list of [char, count]
    for ch in s:
        if stack and stack[-1][0] == ch:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()
        else:
            stack.append([ch, 1])
    return ''.join(ch * cnt for ch, cnt in stack)

def solve(s, k):
    return remove_duplicates(s, k)

CASES = [
    {"s": "deeedbbcccbdaa", "k": 3},
    {"s": "abcd", "k": 2},
    {"s": "aaa", "k": 3},
    {"s": "aa", "k": 1},
    {"s": "abc", "k": 3},
    {"s": "aabbcc", "k": 2},
    {"s": "abbccd", "k": 2},
    {"s": "abcdd", "k": 2},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
