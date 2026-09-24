import sys

def total_n_queens(n: int) -> int:
    if n <= 0:
        return 0
    cols = [False] * n
    diag1 = [False] * (2 * n - 1)  # row + col
    diag2 = [False] * (2 * n - 1)  # row - col + n - 1

    count = 0

    def backtrack(row: int):
        nonlocal count
        if row == n:
            count += 1
            return
        for col in range(n):
            d1 = row + col
            d2 = row - col + n - 1
            if cols[col] or diag1[d1] or diag2[d2]:
                continue
            cols[col] = True
            diag1[d1] = True
            diag2[d2] = True
            backtrack(row + 1)
            cols[col] = False
            diag1[d1] = False
            diag2[d2] = False

    backtrack(0)
    return count


def solve(n: int) -> int:
    return total_n_queens(n)


CASES = [
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 6},
    {"n": 7},
    {"n": 8},
    {"n": 9},
    {"n": 10},
]


if __name__ == '__main__':
    import json

    results = []
    for idx, case in enumerate(CASES):
        out = solve(**case)
        results.append({"id": idx, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, ensure_ascii=False))
