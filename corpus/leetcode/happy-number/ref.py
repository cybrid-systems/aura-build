def sum_of_squares_of_digits(n: int) -> int:
    """Helper to compute sum of squares of digits of n."""
    total = 0
    while n > 0:
        digit = n % 10
        total += digit * digit
        n //= 10
    return total


def solve(n: int) -> bool:
    """Return True if n is a happy number, False otherwise."""
    if n <= 0:
        return False
    seen = set()
    current = n
    while current != 1 and current not in seen:
        seen.add(current)
        current = sum_of_squares_of_digits(current)
    return current == 1


CASES = [
    {"n": 19},
    {"n": 2},
    {"n": 7},
    {"n": 1},
    {"n": 111111111},
    {"n": 0},
    {"n": 4},
    {"n": 100000000},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
