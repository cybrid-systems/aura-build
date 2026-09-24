def solve(ops):
    results = []
    k = None
    window = []
    total = 0
    for op in ops:
        if not op:
            continue
        t = op[0]
        if t == 'M':
            k = int(op[1])
            window = []
            total = 0
        elif t == 'N':
            v = int(op[1])
            window.append(v)
            total += v
            if k is not None and len(window) > k:
                total -= window.pop(0)
            avg = total // len(window)
            results.append(avg)
        elif t == 'G':
            if not window:
                results.append(0)
            else:
                avg = total // len(window)
                results.append(avg)
    return results


CASES = [
    {'ops': [['M', '3'], ['N', '1'], ['N', '10'], ['N', '3'], ['G'], ['N', '5']]},
    {'ops': [['M', '1'], ['N', '5'], ['N', '10'], ['G'], ['N', '-3']]},
    {'ops': [['M', '5'], ['G'], ['N', '2'], ['G'], ['N', '4'], ['N', '-1'], ['N', '0'], ['N', '7']]},
    {'ops': [['M', '3'], ['N', '2'], ['N', '4'], ['N', '6'], ['N', '8'], ['N', '10']]},
    {'ops': [['M', '2'], ['N', '-1'], ['N', '-2'], ['N', '-3']]},
    {'ops': [['M', '10'], ['N', '1'], ['N', '1'], ['N', '1'], ['G']]},
    {'ops': [['M', '3'], ['N', '0'], ['N', '0'], ['N', '0'], ['G'], ['N', '0']]},
    {'ops': [['M', '4'], ['N', '7'], ['N', '-3'], ['N', '2'], ['N', '-1'], ['N', '5'], ['N', '4']]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c['ops'])
        expected = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        out.append({'id': i, 'input': c, 'expected': expected})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
