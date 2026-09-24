# Word Break

## Problem

Given a string `s` and a dictionary `wordDict` containing a list of words, determine if `s` can be segmented into a sequence of one or more dictionary words. Return `True` if such a segmentation exists, otherwise return `False`.

Note that the same word in the dictionary may be reused multiple times in the segmentation.

## Function Signature

```python
def solve(s: str, wordDict: list[str]) -> bool:
    ...
```

## Input / Output Convention

The harness drives `solve(s, wordDict)` directly — no stdin/stdout. Use the harness-provided values and return the boolean result.

Example (illustrative):

```
CASE0=s=leetcode wordDict=[leet, code]
CASE0_EXPECTED=True
CASE1=s=applepenapple wordDict=[apple, pen]
CASE1_EXPECTED=True
CASE2=s=catsandog wordDict=[cats, dog, sand, and, cat]
CASE2_EXPECTED=False
```

## Notes

- The string `s` is non-empty and consists of lowercase English letters.
- The dictionary contains no duplicate words; it may be empty (in which case the answer is always `False` unless `s` is empty).
- Aim for a solution running in roughly `O(n · m · k)` or better, where `n = len(s)`, `m = len(wordDict)`, and `k` is the average word length — a classic DP on prefix positions is expected.
- Consider using a set for `wordDict` lookups to keep each check `O(1)` on average.
