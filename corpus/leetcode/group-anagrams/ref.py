import json
from collections import defaultdict

def solve(strings):
    groups = defaultdict(list)
    for s in strings:
        key = tuple(sorted(s))
        groups[key].append(s)
    return [sorted(group) for group in groups.values()]

CASES = [
    {
        "id": 0,
        "input": {"strings": ["eat", "tea", "tan", "ate", "nat", "bat"]},
    },
    {
        "id": 1,
        "input": {"strings": []},
    },
    {
        "id": 2,
        "input": {"strings": [""]},
    },
    {
        "id": 3,
        "input": {"strings": ["", ""]},
    },
    {
        "id": 4,
        "input": {"strings": ["abc", "bca", "cab", "xyz", "zyx", "yxz"]},
    },
    {
        "id": 5,
        "input": {"strings": ["a"]},
    },
    {
        "id": 6,
        "input": {"strings": ["listen", "silent", "enlist", "hello", "olleh"]},
    },
    {
        "id": 7,
        "input": {"strings": ["ab", "ba", "cd", "dc", "ef"]},
    },
]

def canonicalize(groups):
    return sorted(tuple(sorted(g)) for g in groups)

if __name__ == '__main__':
    results = []
    for case in CASES:
        inp = case["input"]
        result = solve(**inp)
        expected = canonicalize(result)
        results.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(expected, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
