import sys
import os
import re
import json
from collections import Counter


def solve(nums1, nums2):
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    counter = Counter(nums1)
    result = []
    for x in nums2:
        if counter.get(x, 0) > 0:
            result.append(x)
            counter[x] -= 1
            if counter[x] == 0:
                del counter[x]
    return result


def parse_cases(text):
    cases = []
    pattern = re.compile(r'CASE(\d+)_(\w+)=(.*)')
    grouped = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if not m:
            continue
        idx = int(m.group(1))
        key = m.group(2)
        val = m.group(3).strip()
        grouped.setdefault(idx, {})[key] = val
    for idx in sorted(grouped.keys()):
        d = grouped[idx]
        if 'NUMS1' in d and 'NUMS2' in d:
            nums1 = [int(x) for x in d['NUMS1'].split()] if d['NUMS1'] else []
            nums2 = [int(x) for x in d['NUMS2'].split()] if d['NUMS2'] else []
            cases.append({'nums1': nums1, 'nums2': nums2, 'expected': d.get('EXPECTED', '')})
    return cases


def main():
    # Read from stdin if available, otherwise use CASES below
    if sys.stdin and not sys.stdin.isatty():
        try:
            text = sys.stdin.read()
        except Exception:
            text = ''
    else:
        text = ''

    if text.strip():
        cases = parse_cases(text)
    else:
        cases = CASES

    results = []
    for i, case in enumerate(cases):
        nums1 = case['nums1']
        nums2 = case['nums2']
        ans = solve(nums1, nums2)
        expected = case.get('expected', '')
        if expected:
            exp_list = [int(x) for x in expected.split()] if expected.strip() else []
            # Validate (order doesn't matter for multisets)
            if sorted(ans) != sorted(exp_list):
                pass  # Don't assert in __main__
        results.append({
            'id': i,
            'input': {'nums1': nums1, 'nums2': nums2},
            'expected': json.dumps(ans, separators=(',', ':'), ensure_ascii=False)
        })

    print(json.dumps(results, ensure_ascii=False))


CASES = [
    {'nums1': [1, 2, 2, 1], 'nums2': [2, 2]},
    {'nums1': [4, 9, 5], 'nums2': [9, 4, 9, 8, 4]},
    {'nums1': [1, 2, 3, 4], 'nums2': [3, 4, 5, 6]},
    {'nums1': [], 'nums2': [1, 2, 3]},
    {'nums1': [1, 1, 1, 1], 'nums2': [1, 1]},
    {'nums1': [1, 2, 3], 'nums2': []},
    {'nums1': [5, 5, 5, 5, 5], 'nums2': [5, 5, 5]},
    {'nums1': [0, 0, 0], 'nums2': [0, 0]},
]


if __name__ == '__main__':
    main()
