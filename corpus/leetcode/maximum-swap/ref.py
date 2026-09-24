def solve(s: str) -> int:
    digits = list(s)
    n = len(digits)
    
    # Record the last occurrence (rightmost index) of each digit 0-9
    last = [-1] * 10
    for i in range(n):
        last[int(digits[i])] = i
    
    # Greedy: for each position, try to swap in the largest digit
    # that appears later (using the rightmost occurrence).
    for i in range(n):
        current = int(digits[i])
        # Check digits from 9 down to current+1
        for d in range(9, current, -1):
            if last[d] > i:
                # Swap digits[i] with digits[last[d]]
                digits[i], digits[last[d]] = digits[last[d]], digits[i]
                return int(''.join(digits))
        # If current == 9, no larger digit exists, skip
    
    # No beneficial swap found
    return int(s)

CASES = [
    {"s": "2736"},
    {"s": "9973"},
    {"s": "98368"},
    {"s": "0"},
    {"s": "1"},
    {"s": "10"},
    {"s": "1999999999"},
    {"s": "99999"},
]

if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        result = solve(case["s"])
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
