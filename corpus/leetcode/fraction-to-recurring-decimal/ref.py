def solve(numerator: int, denominator: int) -> str:
    if numerator == 0:
        return "0"
    
    neg = (numerator < 0) ^ (denominator < 0)
    
    n = abs(numerator)
    d = abs(denominator)
    
    int_part = n // d
    rem = n % d
    
    result = []
    if neg:
        result.append('-')
    result.append(str(int_part))
    
    if rem == 0:
        return ''.join(result)
    
    result.append('.')
    
    rem_pos = {}
    frac = []
    
    while rem != 0:
        if rem in rem_pos:
            idx = rem_pos[rem]
            frac.insert(idx, '(')
            frac.append(')')
            result.extend(frac)
            return ''.join(result)
        
        rem_pos[rem] = len(frac)
        rem *= 10
        digit = rem // d
        rem = rem % d
        frac.append(str(digit))
    
    result.extend(frac)
    return ''.join(result)


CASES = [
    {"numerator": 1, "denominator": 2},
    {"numerator": 2, "denominator": 1},
    {"numerator": 4, "denominator": 333},
    {"numerator": 0, "denominator": 5},
    {"numerator": -1, "denominator": 2},
    {"numerator": 1, "denominator": -2},
    {"numerator": -1, "denominator": -2},
    {"numerator": -2147483648, "denominator": -1},
    {"numerator": 1, "denominator": 6},
    {"numerator": 22, "denominator": 7},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
