# Concatenated Words

## Problem

You are given a list of **distinct** words consisting only of lowercase English letters. A word is called **concatenated** if it can be formed by concatenating **two or more** other words from the same list. Every word in the list is shorter than 30 characters.

Your task is to return all concatenated words from the list, in any order.

### Examples

**Example 1**

Input list:
```
cat, dog, catsdog, dogcat, catdog
```

- `catsdog` can be split into `cats` + `dog` (but `cats` is not in the list, so not valid)
- `catsdog` can be split into `cat` + `sdog` (not valid)
- `dogcat` can be split into `dog` + `cat` ✅
- `catdog` can be split into `cat` + `dog` ✅

Output:
```
[dogcat, catdog]
```

(We do **not** include `cat`, `dog`, or `catsdog`.)

**Example 2**

Input list:
```
a, b, ab, abc, abcd, abcde
```

- `ab` = `a` + `b` ✅
- `abc` = `a` + `bc`? No. `ab` + `c` ✅
- `abcd` = `a` + `bcd`? No. `ab` + `cd`? No. `abc` + `d` ✅
- `abcde` = `a` + `bcde`? No. `ab` + `cde`? No. `abc` + `de`? No. `abcd` + `e` ✅

Output:
```
[ab, abc, abcd, abcde]
```

## Function Signature

```python
def solve(words: list[str]) -> list[str]:
    ...
```

## Input / Output Convention (Aura harness)

The harness reads no standard input. The values are provided directly via the function call. Test cases are described inline using the `CASE0=...` format below for reference only — your `solve` function is invoked by the grader with the actual `words` list.

```
CASE0=cat dog catsdog dogcat catdog -> [dogcat, catdog]
CASE1=a b ab abc abcd abcde -> [ab, abc, abcd, abcde]
```

Your `solve(words)` must return a list of all concatenated words in `words`.

## Notes

- The result may be empty.
- Words are unique within the input list.
- Order of the output list does not matter, but each concatenated word must appear exactly once.
- The number of words can be up to a few thousand; each word length is at most 29. Aim for a solution where the total work across all words is roughly `O(sum of word lengths)` on average.
- Hint: DFS with memoization on each word — for each prefix, check if it exists in the set; then recurse on the suffix. Cache results so a word is analyzed at most once.
