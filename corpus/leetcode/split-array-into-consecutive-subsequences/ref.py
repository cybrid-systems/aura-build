def solve(nums):
    """
    Determine whether `nums` (sorted non-decreasingly) can be partitioned into
    one or more subsequences of length >= 3 where each subsequence consists of
    consecutive integers.

    Greedy approach using a frequency counter and a "tails" counter.
    For each value v in ascending order:
      - Use as many v's as possible to extend existing subsequences ending at v-1
        (i.e. consume tails[v-1] instances of v).
      - The remaining v's are placed in new subsequences. We need to ensure each
        such new subsequence can extend for at least two more consecutive values
        (v+1, v+2). If freq[v+1] or freq[v+2] is insufficient, return False.
      - Decrement freq[v] and update freq of the next values consumed.
      - Record tails[v] = number of subsequences ending at v.
    """
    from collections import Counter

    freq = Counter(nums)
    tails = Counter()
    for v in sorted(freq.keys()):
        while freq[v] > 0:
            # 1) Extend an existing subsequence ending at v-1 if possible.
            if tails[v - 1] > 0:
                tails[v - 1] -= 1
                freq[v] -= 1
                tails[v] += 1
                continue
            # 2) Otherwise, start a new subsequence v, v+1, v+2.
            if freq[v + 1] > 0 and freq[v + 2] > 0:
                freq[v] -= 1
                freq[v + 1] -= 1
                freq[v + 2] -= 1
                tails[v + 2] += 1
                continue
            # Cannot place this v.
            return False
    return True


CASES = [
    {"nums": [1, 2, 3, 3, 4, 4, 5, 5]},
    {"nums": [1, 2, 3, 3, 4, 4, 5, 5, 6]},
    {"nums": [1, 2, 3, 4, 5]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [1, 1, 2, 2, 3, 3]},
    {"nums": [1, 2, 3]},
    {"nums": [1, 2, 3, 5, 6, 7]},
    {"nums": []},
]


if __name__ == "__main__":
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
