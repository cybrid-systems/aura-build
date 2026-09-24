from typing import List

def solve(n: int) -> List[List[str]]:
    """Return all distinct N-Queens solutions as a list of board configurations.

    Each solution is represented as a list of `n` strings of length `n`
    where 'Q' marks a queen and '.' marks an empty cell.
    """
    results: List[List[str]] = []
    if n <= 0:
        return results

    # `cols[c]` indicates whether column c is occupied.
    cols = [False] * n
    # `diag1[d]` indicates whether the "main" diagonal (row + col == d) is occupied.
    diag1 = [False] * (2 * n - 1)
    # `diag2[d]` indicates whether the "anti" diagonal (row - col + n - 1 == d) is occupied.
    diag2 = [False] * (2 * n - 1)
    # Current partial placement: queen column per row.
    placement: List[int] = [0] * n

    def backtrack(row: int) -> None:
        if row == n:
            # Build a fresh solution from the column placement.
            board: List[str] = []
            for r in range(n):
                row_str = ['.'] * n
                row_str[placement[r]] = 'Q'
                board.append(''.join(row_str))
            results.append(board)
            return
        for col in range(n):
            d1 = row + col
            d2 = row - col + n - 1
            if cols[col] or diag1[d1] or diag2[d2]:
                continue
            cols[col] = True
            diag1[d1] = True
            diag2[d2] = True
            placement[row] = col
            backtrack(row + 1)
            cols[col] = False
            diag1[d1] = False
            diag2[d2] = False

    backtrack(0)
    return results


CASES = [
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 6},
    {"n": 0},
    {"n": 7},
]


if __name__ == '__main__':
    import json

    out = []
    for i, case in enumerate(CASES):
        n = case["n"]
        sols = solve(n)
        expected_strs = [''.join(sol) for sol in sols]
        out.append({
            "id": i,
            "input": {"n": n},
            "expected": json.dumps(expected_strs, separators=(',', ':'), ensure_ascii=False),
        })

    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
