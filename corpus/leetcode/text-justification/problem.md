# Text Justification

## Problem Statement

Given an array of words and a maximum line width `maxWidth`, format the text so that each line has exactly `maxWidth` characters and is fully (left and right) justified.

Rules:

- Pack as many words as possible into each line, in the order given, without exceeding `maxWidth` (including the minimum single space between words).
- For every line except the **last** line and lines containing a **single word**, distribute the extra spaces as evenly as possible between the words. Extra spaces (the remainder when dividing spaces among the gaps) go into the **leftmost** gaps first.
- The **last line** must be **left-justified**: words are separated by a single space, with no leading/trailing extra spaces, and is padded on the right with spaces to reach `maxWidth`.
- A line with a **single word** is left-justified: the word is padded on the right with spaces to reach `maxWidth`.

Return the formatted lines as a list of strings.

## Function Signature

```python
def solve(words: list[str], maxWidth: int) -> list[str]:
    ...
```

## Input / Output Convention

The harness reads a single test case from `STDIN` using a simple `CASE0=...` block:

```
CASE0 = {"words": ["This", "is", "an", "example", "of", "text", "justification."], "maxWidth": 16}
```

- `CASE0["words"]` is a JSON array of strings — the words to justify.
- `CASE0["maxWidth"]` is an integer — the target line width.

The function `solve` must return a list of strings (one per line). The harness prints each returned line on its own line, and prints `-` between test cases if more than one is provided.

## Notes

- Words contain only letters and punctuation; assume no word is longer than `maxWidth`.
- For a line with `k` words and `s` total spaces to distribute, each of the `k - 1` internal gaps gets at least `s // (k - 1)` spaces; the first `s % (k - 1)` gaps receive one additional space.
- Edge cases to consider: a single word on a line, and the final line of the output.
