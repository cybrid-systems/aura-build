import sys
import json


def solve(grid):
    """Update GRID in place for one step of Game of Life using 2/3 markers."""
    if not grid or not grid[0]:
        return grid
    R = len(grid)
    C = len(grid[0])
    for r in range(R):
        row = grid[r]
        for c in range(C):
            # Count live neighbors from the original generation (values 0 or 1)
            live = 0
            for dr in (-1, 0, 1):
                nr = r + dr
                if nr < 0 or nr >= R:
                    continue
                n_row = grid[nr]
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nc = c + dc
                    if nc < 0 or nc >= C:
                        continue
                    # Live neighbor is anything originally alive: 1 (still alive)
                    # or 2 (was alive, now marked dying). We ignore 3 (newly born).
                    v = n_row[nc]
                    if v == 1 or v == 2:
                        live += 1
            cur = row[c]
            if cur == 1:
                if live < 2 or live > 3:
                    row[c] = 2  # dies
            else:  # cur == 0 (cur == 3 cannot exist on entry; cur == 2 impossible on entry)
                if live == 3:
                    row[c] = 3  # becomes alive
    return grid


def _read_cases():
    data = sys.stdin.read().split()
    idx = 0
    cases = []
    while idx < len(data):
        if not data[idx].startswith("CASE"):
            break
        idx += 1
        R = int(data[idx]); idx += 1
        C = int(data[idx]); idx += 1
        grid = []
        for _ in range(R):
            row = [int(data[idx + j]) for j in range(C)]
            idx += C
            grid.append(row)
        cases.append({"grid": grid})
    return cases


CASES = [
    {"grid": [[1]]},
    {"grid": [[0]]},
    {"grid": [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ]},
    {"grid": [
        [1, 1, 1],
        [1, 1, 1],
        [1, 1, 1],
    ]},
    {"grid": [
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1],
    ]},
    {"grid": [
        [1, 1, 0, 0],
        [1, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 1, 1, 0],
    ]},
    {"grid": [[1, 0, 1, 0, 1]]},
    {"grid": [[1, 1], [1, 0]]},
]


def _main():
    # Run built-in CASES
    results = []
    for i, case in enumerate(CASES):
        # Deep copy for each case so re-runs are independent
        grid_copy = [row[:] for row in case["grid"]]
        solve(grid_copy)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(grid_copy, separators=(',', ':'), ensure_ascii=False),
        })
    # Also run any stdin-provided cases if present
    stdin_cases = _read_cases()
    base = len(CASES)
    for j, case in enumerate(stdin_cases):
        grid_copy = [row[:] for row in case["grid"]]
        solve(grid_copy)
        results.append({
            "id": base + j,
            "input": case,
            "expected": json.dumps(grid_copy, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))


if __name__ == '__main__':
    _main()
