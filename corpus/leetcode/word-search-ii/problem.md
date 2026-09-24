# Word Search II

## Problem

You are given an `m x n` board of lowercase letters and a list of `k` dictionary words. Starting from any cell, you may move to one of the 4 adjacent neighbors (up, down, left, right) to trace a path of letters that form a word. A cell may be used at most once per word. Find every word from the dictionary that can be formed on the board.

## Function Signature

```python
def solve(board: list[list[str]], words: list[str]) -> list[str]:
    ...
```

- `board`: a list of `m` rows, each a list of `n` lowercase characters (`1 <= m, n <= 12`).
- `words`: a list of `k` dictionary words (`1 <= k <= 3 * 10^4`, each word length `1 <= |w| <= 10`).
- Return: a list of all dictionary words that appear on the board. The order of the result does not matter; duplicates must not be returned.

## I/O Convention (CASE0 lines)

The harness drives `solve` directly — there is no stdin. When running the harness, the first CASE0 line documents the example:

```
CASE0=board=[["o","a","a","n"],["e","t","a","e"],["i","h","k","r"],["i","f","l","v"]], words=["oath","pea","eat","rain"] -> ["eat","oath"]
```

In the example, `"oath"` traces `o -> a -> t -> h` and `"eat"` traces `e -> a -> t`, while `"pea"` and `"rain"` cannot be formed.

## Notes

- Build a trie (prefix tree) from the dictionary and traverse the board once, pruning branches whose current prefix is not in the trie. This keeps the search near the set of dictionary prefixes rather than the whole board.
- Mark cells visited during the current DFS path (e.g., swap with a sentinel) and restore them on backtrack; do not mutate the input board between independent word searches.
- Returned words must be unique even if the same word appears multiple times in `words`.
