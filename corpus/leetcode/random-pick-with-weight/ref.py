import random
import bisect

def solve(w):
    # Build prefix sums
    prefix = []
    total = 0
    for weight in w:
        total += weight
        prefix.append(total)
    
    # Use a fixed seed for reproducibility
    rng = random.Random(42)
    
    def pickIndex():
        target = rng.randrange(1, total + 1)
        idx = bisect.bisect_left(prefix, target)
        return idx
    
    return {"pickIndex": pickIndex}


CASES = [
    {"w": [1]},
    {"w": [1, 3]},
    {"w": [1, 3, 2, 4]},
    {"w": [10, 20, 30, 40]},
    {"w": [5, 5, 5, 5, 5]},
    {"w": [1] * 10},
    {"w": [1, 100]},
    {"w": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]},
]


if __name__ == '__main__':
    import json
    
    results = []
    for idx, case in enumerate(CASES):
        w = case["w"]
        obj = solve(w)
        # Run pickIndex multiple times and collect distribution
        N_CALLS = 1000
        indices = [obj["pickIndex"]() for _ in range(N_CALLS)]
        # Return the distribution summary (counts per index)
        counts = [0] * len(w)
        for i in indices:
            counts[i] += 1
        # Canonical output: counts list
        result = {"id": idx, "input": {"w": w}, "expected": json.dumps(counts, separators=(',', ':'), ensure_ascii=False)}
        results.append(result)
    
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
