def solve(list1, list2):
    index_map = {s: i for i, s in enumerate(list1)}
    best_sum = float('inf')
    result = []
    for j, s in enumerate(list2):
        if s in index_map:
            total = index_map[s] + j
            if total < best_sum:
                best_sum = total
                result = [s]
            elif total == best_sum:
                result.append(s)
    return result


CASES = [
    {
        "list1": ["Shogun", "Tapioca Express", "Burger King", "KFC"],
        "list2": ["Piatti", "The Grill at Torrey Pines", "Hungry Hunter Steakhouse", "Shogun"],
    },
    {
        "list1": ["Shogun", "Tapioca Express", "Burger King", "KFC"],
        "list2": ["KFC", "Shogun", "Burger King"],
    },
    {
        "list1": ["Shogun", "Tapioca Express", "Burger King", "KFC"],
        "list2": ["Tapioca Express", "Shogun", "Burger King", "KFC"],
    },
    {
        "list1": ["a", "b", "c"],
        "list2": ["d", "e", "f"],
    },
    {
        "list1": ["a", "b", "c"],
        "list2": ["c", "b", "a"],
    },
    {
        "list1": ["a"],
        "list2": ["a"],
    },
    {
        "list1": ["x", "y", "z"],
        "list2": ["z", "y", "x"],
    },
    {
        "list1": ["alpha", "beta", "gamma", "delta"],
        "list2": ["delta", "epsilon", "zeta", "beta", "alpha"],
    },
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        # canonicalize: sort for stable output (problem says order doesn't matter)
        canonical = json.dumps(sorted(result), separators=(',', ':'), ensure_ascii=False)
        inp_str = json.dumps(case, separators=(',', ':'), ensure_ascii=False)
        out.append({"id": i, "input": case, "expected": canonical})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
