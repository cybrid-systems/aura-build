import sys
import json

def solve(s: str, t: str, maxCost: int) -> int:
    if not s:
        return 0
    n = len(s)
    costs = [abs(ord(s[i]) - ord(t[i])) for i in range(n)]
    
    left = 0
    cur_cost = 0
    best = 0
    
    for right in range(n):
        cur_cost += costs[right]
        while cur_cost > maxCost and left <= right:
            cur_cost -= costs[left]
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    
    return best

CASES = [
    {"s": "abcd", "t": "bcdf", "maxCost": 3},
    {"s": "abcd", "t": "cdef", "maxCost": 3},
    {"s": "abcd", "t": "dcba", "maxCost": 0},
    {"s": "aaaa", "t": "bbbb", "maxCost": 10},
    {"s": "a", "t": "z", "maxCost": 25},
    {"s": "a", "t": "z", "maxCost": 24},
    {"s": "xyz", "t": "abc", "maxCost": 100},
    {"s": "abcd", "t": "abdc", "maxCost": 1},
]

if __name__ == '__main__':
    # First run the CASES test suite with JSON output as required by the harness
    results = []
    for i, case in enumerate(CASES):
        s = case["s"]
        t = case["t"]
        mc = case["maxCost"]
        ans = solve(s, t, mc)
        results.append({
            "id": i,
            "input": {"s": s, "t": t, "maxCost": mc},
            "expected": json.dumps(ans, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))

    # Then handle stdin CASE-style input for the actual problem
    out_lines = []
    for line in sys.stdin:
        line = line.rstrip('\n')
        if not line:
            continue
        # Format: CASE<i>=<s>,<t>,<maxCost>
        if '=' not in line:
            continue
        eq_idx = line.index('=')
        header = line[:eq_idx]
        rest = line[eq_idx+1:]
        # Split on first two commas only
        parts = rest.split(',', 2)
        if len(parts) != 3:
            continue
        s_val, t_val, mc_val = parts[0], parts[1], parts[2]
        try:
            mc_int = int(mc_val)
        except ValueError:
            continue
        ans = solve(s_val, t_val, mc_int)
        out_lines.append(f"{header}={ans}")
    
    if out_lines:
        sys.stdout.write('\n'.join(out_lines) + '\n')
