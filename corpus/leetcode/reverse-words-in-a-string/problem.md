# Reverse Words in a String

## Problem

Given a string `s`, reverse the order of the words in the string.

A **word** is defined as a maximal contiguous sequence of non-space characters. Words are separated by one or more spaces.

The reversed string should:
- Have the words in reverse order.
- Separate each pair of adjacent words by exactly **one** space.
- Contain **no leading or trailing spaces**.

Write a function that returns this reversed string.

### Function Signature

```lisp
(defun solve (s)
  ;; ...
  )
```

## Input / Output Convention

The function receives a single string `s` and returns a single string. The harness calls it via:

```
CASE0=s = "  the sky   is blue  "
CASE0=ans = "blue is sky the"
```

That is, lines of the form `CASE<n>=<label> = <value>`, where `s = ...` is the input and `ans = ...` is the expected output.

## Notes

- You may assume `s` contains only printable ASCII letters, digits, punctuation, and spaces — no newline characters inside `s`.
- The input may contain zero or more leading/trailing spaces and any number of consecutive spaces between words; the output must be compact.
- If `s` contains no words (e.g., it is empty or consists entirely of spaces), return an empty string `""`.
- Do not use any external string-splitting or regex libraries beyond what your language provides for basic whitespace handling.

## Examples

| Input | Output |
|---|---|
| `"the sky is blue"` | `"blue is sky the"` |
| `"  hello world  "` | `"hello world"` |
| `"a   b   c"` | `"c b a"` |
| `"   "` | `""` |
