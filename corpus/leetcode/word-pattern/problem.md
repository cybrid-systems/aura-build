# Word Pattern

## Problem

You are given a two-line input containing a **pattern** (first line) and a **sentence** (second line). The pattern consists of lowercase English letters; the sentence consists of lowercase words separated by single spaces. Determine whether the sentence follows the pattern, i.e., whether there exists a one-to-one mapping between the characters of the pattern and the words of the sentence such that the characters appear in the same order as the corresponding words.

A valid mapping must be **bijective**:
- Each pattern character maps to exactly one word.
- Each word is mapped to by exactly one pattern character.

Return `YES` if the pattern matches the sentence, otherwise return `NO`.

## Function Signature

```clojure
(solve pattern sentence)
```

- `pattern` — a string of lowercase letters (e.g. `"abba"`).
- `sentence` — a string of lowercase words separated by single spaces (e.g. `"dog cat cat dog"`).

## Input Convention

The harness reads stdin as plain text and passes the two lines to `solve`:

```
CASE0=abba
CASE0=dog cat cat dog
```

(The `CASE0=` prefix is the harness label; the actual values follow the `=` sign.)

For the example above the expected output is `YES` (the mapping `a -> dog`, `b -> cat` is bijective and preserves order).

## Examples

| Pattern   | Sentence                  | Output |
|-----------|---------------------------|--------|
| `abba`    | `dog cat cat dog`         | YES    |
| `abba`    | `dog cat cat fish`        | NO     |
| `aaaa`    | `dog cat cat dog`         | NO     |
| `abc`     | `one two three`           | YES    |
| `abc`     | `one one one`             | NO     |

## Notes

- The number of words in the sentence must equal the length of the pattern; otherwise the answer is `NO`.
- Use two hash maps (or equivalent structures) to enforce the bijective constraint in both directions.
- The words are guaranteed to be non-empty and lowercase; no punctuation is involved.
