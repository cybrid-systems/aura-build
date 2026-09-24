import json

def solve(ops):
    freq = {}
    group = {}
    max_freq = 0
    result = []
    for op in ops:
        if op[0] == 'push':
            x = op[1]
            f = freq.get(x, 0) + 1
            freq[x] = f
            if f not in group:
                group[f] = []
            group[f].append(x)
            if f > max_freq:
                max_freq = f
        else:  # pop
            x = group[max_freq].pop()
            result.append(x)
            freq[x] -= 1
            if not group[max_freq]:
                max_freq -= 1
    return result


CASES = [
    # The provided sample case
    {"ops": [["push", 1], ["push", 2], ["push", 2], ["push", 1], ["push", 1],
             ["pop"], ["pop"], ["pop"]]},
    # Single element
    {"ops": [["push", 5], ["pop"]]},
    # All same value
    {"ops": [["push", 7], ["push", 7], ["push", 7], ["pop"], ["pop"], ["pop"]]},
    # Distinct values: stack order on pops
    {"ops": [["push", 1], ["push", 2], ["push", 3], ["pop"], ["pop"], ["pop"]]},
    # Interleaved: ties at higher frequency
    {"ops": [["push", 1], ["push", 2], ["push", 1], ["push", 2], ["pop"],
             ["pop"], ["pop"], ["pop"]]},
    # After many pops, new pushes raise max_freq again
    {"ops": [["push", 1], ["pop"], ["push", 1], ["push", 1], ["push", 1],
             ["pop"], ["pop"], ["pop"]]},
    # Negative values
    {"ops": [["push", -1], ["push", -2], ["push", -1], ["pop"], ["pop"],
             ["pop"]]},
    # Larger interleaving to validate tie-breaking by recency
    {"ops": [["push", 1], ["push", 2], ["push", 3], ["push", 2], ["push", 3],
             ["push", 3], ["pop"], ["pop"], ["pop"], ["pop"], ["pop"],
             ["pop"]]},
]


if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["ops"])
        canonical = "|".join(str(v) for v in res)
        out.append({"id": i, "input": c, "expected": canonical})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
