import sys
import json

def solve(s):
    ans = 0
    for ch in s:
        ans = ans * 26 + (ord(ch) - ord('A') + 1)
    return ans

CASES = [
    {"s": "A"},
    {"s": "Z"},
    {"s": "AA"},
    {"s": "AB"},
    {"s": "AZ"},
    {"s": "BA"},
    {"s": "ZZ"},
    {"s": "AAA"},
    {"s": "ZY"},
]

def parse_input():
    cases = []
    for line in sys.stdin:
        line = line.strip()
        if not line or '=' not in line:
            continue
        # Expect CASE0=<s> format
        _, val = line.split('=', 1)
        cases.append({"s": val})
    return cases

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'harness':
        # Run via stdin harness
        cases = parse_input()
        results = []
        for c in cases:
            r = solve(c["s"])
            results.append(json.dumps({"id": 0, "input": c, "expected": json.dumps(r, separators=(',', ':'), ensure_ascii=False)}, ensure_ascii=False))
        # Print one per line as plain outputs
        for r in results:
            # The harness expects results, we print r directly
            print(r)
    else:
        # Standard mode: run solve on CASES and print JSON array
        out = []
        for i, c in enumerate(CASES):
            r = solve(c["s"])
            out.append({"id": i, "input": c, "expected": json.dumps(r, separators=(',', ':'), ensure_ascii=False)})
        print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
