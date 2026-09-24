import json


def solve(n):
    if n <= 2:
        return 0
    # Sieve of Eratosthenes: mark composites up to n-1
    sieve = bytearray([1]) * n
    sieve[0] = 0
    sieve[1] = 0
    import math
    limit = int(math.isqrt(n - 1)) + 1
    for i in range(2, limit):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start:n:step] = b'\x00' * ((n - 1 - start) // step + 1)
    return int(sum(sieve))


CASES = [
    {"n": 10},
    {"n": 0},
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 5},
    {"n": 100},
    {"n": 1000},
]


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
