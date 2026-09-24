# Design Add and Search Words Data Structure

## Problem Statement

Design a data structure that supports the addition of words and the searching of words with wildcard characters.

Implement a class `WordDictionary` with the following methods:

- `addWord(word)`: Adds a word to the data structure. It can be matched later.
- `search(word)`: Returns `true` if there is any string in the data structure that matches `word`, and `false` otherwise.
  - The word may contain dots `'.'` where dots can be matched with any single character (lowercase letter).

You are given `n` operations consisting of either:
- `add <word>` — add a word to the dictionary, or
- `search <word>` — search whether such a word exists.

For each `search` operation, output `1` if it matches an existing word, otherwise `0`.

## Input

The first line contains an integer `n` — the number of operations (`1 ≤ n ≤ 10^4`).

Each of the next `n` lines describes an operation:
- `add <word>` — a word `w` consisting of lowercase English letters (`1 ≤ |w| ≤ 25`)
- `search <word>` — a word `w` consisting of lowercase English letters and `'.'` (`1 ≤ |w| ≤ 25`)

## Output

For each `search` operation, print `1` if a matching word exists in the dictionary, otherwise `0`. Each answer must be on its own line, in the same order as the `search` operations appear in the input.

## Function Signature Hint

```lisp
(defun solve (n ops)
  ;; ops: list of pairs (op . word) where op is either 'add or 'search
  ;; returns: list of 0/1 answers for each 'search op, in order
  )
```

## I/O Convention (Aura harness, stdin-less)

```
CASE0=5
CASE0_OPS=[["add","bad"],["add","dad"],["add","mad"],["search","pad"],["search","bad"]]
CASE0_OUT=[0,1]
```

## Notes

- Use a trie (prefix tree) where each node holds up to 26 children and a flag indicating whether a word ends at that node.
- For `search`, when encountering a `'.'`, you must recursively explore all 26 possible children at that position; otherwise perform a direct child lookup.
- The total sum of word lengths across all operations is bounded by `n * 25 = 2.5 * 10^5`, which fits comfortably in memory.
- Answers must be produced in the order the `search` operations appear in the input.
