import sys
import json

def zigzag_convert(s: str, numRows: int) -> str:
    if numRows <= 1 or numRows >= len(s):
        return s
    rows = [''] * numRows
    idx, step = 0, 1
    for ch in s:
        rows[idx] += ch
        if idx == 0:
            step = 1
        elif idx == numRows - 1:
            step = -1
        idx += step
    return ''.join(rows)

def solve(numRows, s):
    return zigzag_convert(s, numRows)

CASES = [
    {"numRows": 3, "s": "PAYPALISHIRING"},
    {"numRows": 4, "s": "PAYPALISHIRING"},
    {"numRows": 1, "s": "PAYPALISHIRING"},
    {"numRows": 2, "s": "PAYPALISHIRING"},
    {"numRows": 3, "s": "A"},
    {"numRows": 4, "s": "AB"},
    {"numRows": 5, "s": "ABCDEFGHIJKLMN"},
    {"numRows": 6, "s": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
