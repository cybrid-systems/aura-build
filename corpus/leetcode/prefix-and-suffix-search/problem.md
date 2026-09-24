# Prefix and Suffix Search

## Problem

Design a data structure that supports storing a collection of words and efficiently answering queries of the form: "what is the word with the largest index in the collection that has a given prefix `pref` AND a given suffix `suff`?"

Words are indexed starting from 0 in the order they are inserted. If multiple words match the same prefix–suffix pair, return the one with the largest index (i.e., the one inserted most recently). If no inserted word matches, return `-1`.

Implement a class (or set of functions) that supports:

- **Insert** a word with a given index.
- **Query**: given a `prefix` and `suffix`, return the largest index `i` such that the word at index `i` starts with `prefix` and ends with `suffix`.

## Function Signature

```
solve
  -> make_prefix_suffix_search
  :: (Int) -> (String -> Int -> IO ()) -> (String -> String -> IO Int)
```

The harness will call `make_prefix_suffix_search` to obtain the two operations. The first argument is a hint for the expected number of words (can be ignored if desired).

## Input / Output Convention

The input describes a sequence of operations. Each line has one of the following forms:

```
CASE0=INSERT <index> <word>
CASE0=QUERY <prefix> <suffix>
```

- `INSERT <index> <word>` — insert `word` with the given integer index. Words are non-empty strings consisting of lowercase letters `a`–`z`.
- `QUERY <prefix> <suffix>` — perform a query and output the result.

For every `QUERY` line, your program must print the answer on its own line, in the order the queries appear.

## Example

Input:
```
CASE0=INSERT 0 apple
CASE0=INSERT 1 apply
CASE0=INSERT 2 ape
CASE0=INSERT 3 applet
CASE0=QUERY ap le
CASE0=QUERY a e
CASE0=QUERY b x
```

Output:
```
3
2
-1
```

Explanation:
- Query `ap le`: words starting with `ap` and ending with `le` → only "applet" (index 3). Answer `3`.
- Query `a e`: words starting with `a` and ending with `e` → "ape" (index 2). Answer `2`.
- Query `b x`: no matching word. Answer `-1`.

## Notes

- Index values in `INSERT` are non-negative integers and may repeat across different words.
- A word trivially matches the empty prefix and the empty suffix.
- Aim for efficient queries; brute force over all stored words per query will be too slow for large inputs.
