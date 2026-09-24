# Word Ladder

## Statement

Given two words, `beginWord` and `endWord`, and a dictionary `wordList` containing a set of words, find the length of the shortest transformation sequence from `beginWord` to `endWord`.

Rules:
- Only one letter can be changed at a time.
- Each transformed word must exist in the `wordList` (including `endWord` itself, if reachable).
- `beginWord` is **not** part of `wordList` unless specified otherwise.
- Return `0` if no valid transformation sequence exists.

## Function Signature

```clojure
(defn solve [begin-word end-word word-list]
  ;; returns the length of the shortest transformation sequence,
  ;; or 0 if no sequence exists
  )
```

## Input Convention

The harness invokes `solve` directly with arguments parsed from the input. Input format:

```
CASE0=beginWord
CASE0=endWord
CASE0=w1,w2,w3,...,wN
```

- Line 1: `beginWord`
- Line 2: `endWord`
- Line 3: comma-separated words making up the `wordList`

### Example Input

```
CASE0=hit
CASE0=cog
CASE0=hot,dot,dog,lot,log,cog
```

### Example Output

```
CASE0=5
```

(The shortest sequence is `hit -> hot -> dot -> dog -> cog`, length 5.)

## Notes

- Treat all words as case-sensitive.
- The `wordList` may contain duplicates; remove them before processing.
- If `endWord` is not present in `wordList`, immediately return `0`.
- Aim for O(L × N) time using BFS with intermediate-state neighbors (e.g., generic states like `h*t`, `*ot`, `ho*`) to avoid O(N²) pairwise comparisons.
