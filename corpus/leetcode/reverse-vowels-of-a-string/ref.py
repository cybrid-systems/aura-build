def solve(s):
    vowels = set('aeiou')
    s_list = list(s)
    left, right = 0, len(s_list) - 1
    while left < right:
        if s_list[left] not in vowels:
            left += 1
            continue
        if s_list[right] not in vowels:
            right -= 1
            continue
        s_list[left], s_list[right] = s_list[right], s_list[left]
        left += 1
        right -= 1
    return ''.join(s_list)


CASES = [
    {"s": "hello"},
    {"s": "leetcode"},
    {"s": "aA"},
    {"s": ""},
    {"s": "a"},
    {"s": "bcdfg"},
    {"s": "aeiou"},
    {"s": "a1e2i3o4u5"},
    {"s": "racecar"},
    {"s": "Design a program to reverse vowels"},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["s"])
        results.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, ensure_ascii=False))
