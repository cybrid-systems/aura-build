# Replace Words

## Problem

In English, many words can be formed by adding a prefix (called a **root**) to a shorter word. For example, `"a"`, `"al"`, and `"ali"` are all valid roots of the word `"alice"`. Given a dictionary of root words and a sentence composed of lowercase words separated by single spaces, replace every word in the sentence with its shortest root from the dictionary. If no root of a word is present in the dictionary, leave the word unchanged.

## Function Signature

```lisp
(defun solve (roots sentence) ...)
```

- `roots` — a list of strings representing the dictionary of root words.
- `sentence` — a string of lowercase words separated by single spaces.
- Returns a new string with each word replaced by its shortest matching root (or unchanged if no match exists).

## Input / Output Convention

The harness feeds parameters to `solve` via these special lines (no stdin, no stdout):

```
CASE0_NAME=replace-words
CASE0_ROOTS=a,al,ali,alice,b,br,bre,brea,break,breaki,breakin,breakinc,breaking,c
CASE0_SENTENCE=alice is breaking the cable
CASE0_EXPECTED=al is break the c
```

Multiple cases may be provided (`CASE1_…`, `CASE2_…`, …). The runner invokes `solve` for each case and compares the returned string against the matching `CASE<n>_EXPECTED`.

## Notes

- A word may have several prefixes present in `roots`; always pick the **shortest** one.
- If a word is itself in `roots`, it is its own shortest root and should be used as-is.
- Words are lowercase and contain only `a–z`; assume the input is well-formed.
- Expected output words are separated by single spaces, with no leading or trailing space.
