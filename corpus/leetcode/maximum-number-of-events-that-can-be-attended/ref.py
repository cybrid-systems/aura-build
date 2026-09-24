import bisect

def solve(events):
    if not events:
        return 0
    events = sorted(events, key=lambda x: x[1])
    used = []  # sorted list of days already taken
    count = 0
    for s, e in events:
        # find earliest day >= s that isn't taken and <= e
        idx = bisect.bisect_left(used, s)
        candidate = s if idx == len(used) else (used[idx] if idx < len(used) else None)
        # We need the smallest unused day >= s
        # Strategy: try days starting from s, skipping any that are in `used`
        # Better: find smallest d in [s,e] such that d not in used.
        # Use bisect to find position; candidate = used[idx] if exists, else None
        # If idx < len(used) and used[idx] is the next taken day after s,
        # then we want a day strictly less than used[idx].
        # But we also must have candidate <= e.
        if idx < len(used):
            # used[idx] is the smallest taken day >= s
            # We need a day in [s, used[idx]-1]
            d = s
        else:
            d = s
        # Find smallest d >= s with d <= e and d not in used.
        # Walk: d = s; while d in used and d <= e: d += 1.
        # To do efficiently, jump over consecutive taken days.
        # Simpler approach using bisect:
        # The answer is: if idx < len(used) and used[idx] == s, then s is taken, try s+1, etc.
        # Use a loop jumping over contiguous block at idx.
        d = s
        # Skip over all taken days >= s that are contiguous starting at idx
        while idx < len(used) and used[idx] == d:
            d += 1
            idx += 1
        if d <= e:
            count += 1
            bisect.insort(used, d)
    return count

CASES = [
    {"events": [[1,2],[2,3],[3,4]]},
    {"events": [[1,4],[4,4],[2,2],[3,4],[1,1]]},
    {"events": [[1,100000]]},
    {"events": []},
    {"events": [[1,1],[1,1],[1,1]]},
    {"events": [[1,2],[1,2],[3,3]]},
    {"events": [[1,5],[2,3],[3,4],[4,5]]},
    {"events": [[5,5],[1,5],[2,4],[3,3]]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["events"])
        out.append({"id": i, "input": c, "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
