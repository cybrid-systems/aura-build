def solve(m, n):
    # Handle 64-bit unsigned inputs: mask to 64 bits
    mask64 = (1 << 64) - 1
    m = m & mask64
    n = n & mask64
    
    if m == n:
        return m
    
    # Find the longest common prefix of m and n
    # The result is m with all bits cleared from the position where m and n first differ
    shift = 0
    a, b = m, n
    while a != b and a != 0 and b != 0:
        # Count trailing zeros of XOR
        xor = a ^ b
        # Find lowest set bit position
        # Using bit_length-1 to find position
        low_bit = xor & (-xor)  # isolate lowest set bit
        # Count how many trailing zeros
        t = low_bit.bit_length() - 1
        shift += t
        a >>= t
        b >>= t
        if a == b:
            break
        # shift right by 1 to continue
        shift += 1
        a >>= 1
        b >>= 1
    
    # The answer is m shifted left so that only the common prefix remains
    # Actually simpler approach: keep shifting both right until equal, then shift back
    pass

def solve(m, n):
    mask64 = (1 << 64) - 1
    m = m & mask64
    n = n & mask64
    
    if m == n:
        return m
    
    shift = 0
    a, b = m, n
    while a != b:
        a >>= 1
        b >>= 1
        shift += 1
    
    return (a << shift) & mask64

CASES = [
    {"m": 5, "n": 7},
    {"m": 0, "n": 0},
    {"m": 1, "n": 1 << 63},
    {"m": 1 << 63, "n": 1 << 63},
    {"m": 0, "n": (1 << 64) - 1},
    {"m": 0, "n": 1},
    {"m": 12, "n": 15},
    {"m": 1 << 63, "n": (1 << 64) - 1},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({"id": i, "input": case, "expected": str(out)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
