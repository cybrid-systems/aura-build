import json
import sys

def parse_interval(s):
    # "start end" -> [start, end]
    parts = s.split()
    return [int(parts[0]), int(parts[1])]

def parse_input(data):
    # data is a list with two elements: list of interval strings, list of interval strings
    a = [parse_interval(x) for x in data[0]]
    b = [parse_interval(x) for x in data[1]]
    return a, b

def solve(*args):
    # Accept either two lists or a single combined input
    if len(args) == 1:
        a, b = parse_input(args[0])
    else:
        a, b = args[0], args[1]
    
    result = []
    i, j = 0, 0
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0])
        hi = min(a[i][1], b[j][1])
        if lo <= hi:
            if result and lo <= result[-1][1]:
                # merge with previous (closed intervals, touching merges)
                result[-1][1] = max(result[-1][1], hi)
            else:
                result.append([lo, hi])
        # advance the one with smaller end
        if a[i][1] < b[j][1]:
            i += 1
        elif a[i][1] > b[j][1]:
            j += 1
        else:
            i += 1
            j += 1
    return result


CASES = [
    {"a": [], "b": []},
    {"a": [[0,0]], "b": [[0,0]]},
    {"a": [[0,5]], "b": [[3,8]]},
    {"a": [[0,2],[5,10],[13,23],[24,25]], "b": [[1,5],[8,12],[15,24],[25,26]]},
    {"a": [[1,2],[3,4]], "b": [[2,3]]},
    {"a": [[0,5],[7,10]], "b": [[5,7]]},
    {"a": [[0,10]], "b": [[2,5],[11,12]]},
    {"a": [[1,3],[5,7],[9,11]], "b": [[2,4],[6,8],[10,12]]},
]


if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        a = case["a"]
        b = case["b"]
        result = solve(a, b)
        encoded_input = {
            "a": [[f"{x[0]} {x[1]}" for x in a]],
            "b": [[f"{x[0]} {x[1]}" for x in b]],
        }
        out.append({
            "id": idx,
            "input": encoded_input,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
