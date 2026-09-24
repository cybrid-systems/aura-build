# Number of Islands

You are given a 2D grid of size `H x W`, where each cell contains either `'1'` (land) or `'0'` (water). Two cells belong to the **same island** if they are 4-connected (sharing an edge) and both contain `'1'`. Determine how many distinct islands exist in the grid.

## Input

- `H W` — height and width of the grid (1 ≤ H, W ≤ 100).
- Followed by `H` lines, each containing a string of length `W` composed of `'0'` and `'1'`.

## Output

- A single integer: the number of distinct islands.

## Examples

```
CASE0=2
```

```
CASE0=3
```

## Function Signature (target language: standard)

```
int solve(int H, int W, vector<string> grid)
```

## I/O Convention (stdin-less)

The harness writes zero or more `CASE0=` lines to the function and reads back the returned integer. Each `CASE0=` line specifies the value of the respective input argument in declaration order; for multi-row arguments (like `grid`), multiple lines represent successive elements of the structure. No prompts, no extra whitespace.

## Notes

- Use BFS with a queue to flood-fill each unvisited `'1'` and mark visited cells.
- The grid may be modified in place (replacing `'1'` with `'0'`) to track visited cells, or an auxiliary `visited` array may be used.
- Boundary cells (edges and corners) are handled like any other cell; out-of-bounds moves are simply skipped.
- Complexity target: `O(H * W)` time and space.
