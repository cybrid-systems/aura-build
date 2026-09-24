# Word Break II

## Problem

Given a string `s` and a dictionary of unique words `wordDict`, return **all** possible sentences formed by appending a space between each pair of words such that every word in the sentence belongs to the dictionary. Each sentence should be returned as a single string with words separated by a single space.

The input is guaranteed to satisfy the property that `s` can be segmented into dictionary words (i.e., at least one valid sentence exists). However, some prefixes of `s` may not be segmentable; in that case, you should skip those branches (do not generate partial/invalid sentences).

You may assume:

- `1 <= s.length <= 60`
- `1 <= wordDict.length <= 1000`
- `1 <= wordDict[i].length <= 20`
- All strings consist of lowercase English letters only.
- All `wordDict[i]` are unique.

## Function Signature

```clojure
(defn solve [s word-dict] ...)
```

- `s` — the input string (string).
- `word-dict` — the list of dictionary words (vector of strings).
- Returns a vector of strings, each string being a valid sentence.

## Input Convention

The harness is **stdin-less**. Test cases are provided directly to the function. For documentation, an equivalent input format is:

```
CASE0=s="catsanddog" wordDict=["cat","cats","and","sand","dog"]
CASE0_EXPECTED=["cats and dog","cat sand dog"]
CASE1=s="pineapplepenapple" wordDict=["apple","pen","applepen","pine","pineapple"]
CASE1_EXPECTED=["pine apple pen apple","pineapple pen apple","pine applepen apple"]
CASE2=s="catsandog" wordDict=["cats","dog","sand","and","cat"]
CASE2_EXPECTED=[]
```

The order of sentences in the output vector does **not** matter.

## Notes

- Use memoization on the index into `s` to avoid recomputation across overlapping subproblems; without it, the worst case (e.g., all single-letter words) explodes exponentially.
- A `can-break[i]` prefix check (standard Word Break I DP) is a useful pruning step to skip dead-end prefixes before recursing, but is not strictly required given the guarantee of at least one solution.
- A word can be used multiple times; only the strings need to be unique in the dictionary.
- Return an empty vector (not `nil`) when no valid sentence exists — the test harness checks for `CASE0_EXPECTED=[]` style assertions.
