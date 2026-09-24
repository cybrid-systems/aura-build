# Word Ladder II

## Problem

Given two words, `beginWord` and `endWord`, and a dictionary `wordList` containing a set of words, find **all** shortest transformation sequences from `beginWord` to `endWord`. A transformation sequence is a sequence of words `w1, w2, ..., wk` such that:

- `w1 = beginWord`
- `wk = endWord`
- Each `wi+1` differs from `wi` by exactly one letter
- Every `wi` (for `1 < i < k`) belongs to `wordList`

Only one letter can be changed at a time, and each transformed word must exist in the `wordList` (including `endWord`). Return all such sequences in any order; each sequence is a list of strings. If no valid sequence exists, return an empty list.

## Function Signature

```haskell
solve beginWord endWord wordList -> [[String]]
```

The implementation should be provided in a function named `solve` that receives three arguments:

- `beginWord :: String` — the starting word
- `endWord :: String` — the target word
- `wordList :: [String]` — the list of allowed intermediate words

It must return `[[String]]`, i.e., a list of all shortest transformation sequences.

## Input Convention

The harness will define constants directly (no stdin):

```aura
CASE0_BEGIN="hit"
CASE0_END="cog"
CASE0_LIST=["hot","dot","dog","lot","log","cog"]
```

Your `solve` function is called with these values, and must return the expected list of shortest sequences.

## Output Convention

Output is printed as a JSON-compatible list of lists of strings, one per line per sequence (or a pretty-printed list). Example for the case above:

```
[["hit","hot","dot","dog","cog"],["hit","hot","lot","log","cog"]]
```

## Notes

- All words have the same length.
- `beginWord` is **not** included in `wordList`; only intermediate words and `endWord` are.
- If `endWord` is not in `wordList`, return `[]`.
- The result must contain **only** the shortest sequences — longer valid paths must be omitted.
- Approach hint: BFS from `beginWord` to determine shortest distances, then DFS/backtrack from `endWord` along edges of minimum distance to enumerate all shortest paths.
