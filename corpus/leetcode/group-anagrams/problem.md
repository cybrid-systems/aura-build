# Group Anagrams

## Problem

Given an array of strings, group together the strings that are anagrams of each other. Two strings are anagrams if they contain the same characters with the same multiplicities (order does not matter). The grouping should partition the input — every string appears in exactly one group, and each group consists entirely of mutual anagrams.

## Function Signature

```lisp
(solve STRINGS) -> GROUPS
```

- `STRINGS` — a list of strings (each string is a list of characters or equivalent sequence type).
- `GROUPS` — a list of groups, where each group is a list of strings that are anagrams of one another. The order of groups and the order of strings within a group does not matter.

## Input / Output Convention

The harness reads from a stub `CASE0` block in `aura.lisp`:

```
CASE0 = (
  :input  ("eat" "tea" "tan" "ate" "nat" "bat")
  :output (("eat" "tea" "ate") ("tan" "nat") ("bat"))
)
```

- `:input` is the list of strings passed as `STRINGS`.
- `:output` is the expected `GROUPS` value. Your solution must return a value that is a setwise match — i.e. equal as a multiset of groups, each group equal as a multiset of strings — though the reference comparison is case-by-case.

## Notes

- Strings may contain only lowercase English letters, but treat the problem generically: equality of two strings as anagrams means equal character counts regardless of case policy used by your implementation.
- Empty strings, if present, should all group together as anagrams of one another.
- Group ordering and intra-group ordering are not significant for correctness, but producing a stable, deterministic output helps debugging.
