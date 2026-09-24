# Implement Trie (Prefix Tree)

## Problem

Design and implement a **Trie** (also known as a prefix tree) data structure that supports the following operations on lowercase English letters (`'a'` to `'z'`):

- `insert(word)`: Insert a word into the trie.
- `search(word)`: Return `True` if the word is in the trie (i.e., was previously inserted), and `False` otherwise.
- `starts_with(prefix)`: Return `True` if there is any previously inserted word that has the given prefix, and `False` otherwise.

You will be given a sequence of operations to perform. For each operation, produce the corresponding output where applicable.

## Function Signature

```python
def solve(operations: list[list[str]]) -> list[Union[bool, None]]:
    ...
```

The `solve` function receives a list of operations, where each operation is a list of strings:

- `["insert", word]` — insert `word` into the trie. No output is produced.
- `["search", word]` — return `True` or `False`.
- `["starts_with", prefix]` — return `True` or `False`.

The returned list should contain the results for each `search` and `starts_with` operation in order; `insert` operations contribute no entry to the output list.

## Input Format

The harness drives the solution through a `CASE0` line containing the operation list. Each operation is provided on its own line as comma-separated tokens:

```
CASE0=insert apple;search apple;starts_with app;insert app;search app;search ap;starts_with ap
```

Operations are separated by `;` and each operation begins with the command name followed by its argument.

## Output Format

For each query operation (`search` or `starts_with`), output a line containing `True` or `False`. The number of output lines equals the number of query operations in the input.

## Notes

- All words and prefixes consist only of lowercase English letters (`'a'–'z'`).
- The trie should treat each character independently; `search("apple")` should return `True` only after `insert("apple")` has been called.
- `starts_with` returns `True` even if the prefix itself was never inserted, as long as some previously inserted word begins with that prefix.
- Assume the input is well-formed; no error handling for malformed operations is required.
