import sys, json

def solve(nums):
    xor_all = 0
    for v in nums:
        xor_all ^= v
    # isolate lowest set bit
    diff_bit = xor_all & -xor_all
    a, b = 0, 0
    for v in nums:
        if v & diff_bit:
            a ^= v
        else:
            b ^= v
    return [a, b]

CASES = [
    {"nums": [1, 2, 1, 3, 2, 5]},
    {"nums": [-1, 0]},
    {"nums": [0, 1]},
    {"nums": [1, 2, 3, 4, 5, 5, 3, 4]},
    {"nums": [7, 7, 8, 9, 10, 9]},
    {"nums": [1000000000, -1000000000, 5, 5, 6, 6]},
    {"nums": [42, 42, 0, 0, 1, 2]},
    {"nums": [3, 3, 4, 5]},
]

if __name__ == '__main__':
    results = []
    for i, c in enumerate(CASES):
        out = solve(c["nums"])
        results.append({
            "id": i,
            "input": c,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    sys.stdout.write(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
