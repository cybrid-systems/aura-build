# Remove All Adjacent Duplicates in String II

## Problem

You are given a string `s` (lowercase English letters) and an integer `k`. Repeatedly scan `s` from left to right and, whenever you find a **contiguous group of exactly `k` identical characters**, delete that group. After each deletion, the remaining characters may shift together and form new groups of `k` identical characters, which must also be deleted. Continue until the string contains no such group.

Return the final, stable string.

### Example

Input:
```
s = "pbbcggttchhhh", k = 3
```

Step-by-step:
1. `pbbcggttchhhh` → `pbbcggttc`       (remove `hhh`)
2. `pbbcggttc`    → `pbggttc`           (no 3-group exists; wait, scan: `bb` is only 2, `gg` is 2, `tt` is 2 — none. Actually re-scan: `pbbcggttc` has no 3-equal run. So stable.)

Wait, let's pick a clearer example:

Input:
```
s = "abcd", k = 2
```
Output: `abcd` (no groups of size 2).

Input:
```
s = "deeedbbcccbdaa", k = 3
```
- `deeedbbcccbdaa` → remove `eee` → `ddbbcccbdaa`
- `ddbbcccbdaa`   → remove `bbb` → `ddcccbdaa`
- `ddcccbdaa`     → remove `ccc` → `dddbaa`  (no — `ddd` is size 3, remove it too)
- → `baa`  (no group of size 3)

Output: `baa`

## Function Signature

```lisp
(defun solve (s k) ...)
```

- `s` — string (a list of characters or a string)
- `k` — positive integer

Return the resulting stable string.

## Input / Output (Harness Convention)

The harness feeds parameters on stdin as label/value lines. You read them and print one line: the answer.

```
CASE0=s=pbbcggttchhhh
CASE0=k=3
----
CASE0_ANS=pbc
```

(Each `CASEi=` block defines one test case; `CASEi_ANS=` is the expected output the harness compares against.)

For multiple cases, additional `CASE1=...`, `CASE2=...` blocks follow.

## Notes

- Use a stack where each frame stores a character and a count of how many consecutive copies of it are currently "open". When the top count reaches `k`, pop the frame (the group is deleted).
- After processing all characters, concatenate each stored character repeated by its count.
- Empty output is valid — print an empty line.
- Constraints typically allow `O(|s|)` time and space.
- Edge cases: `k = 1` deletes everything; `k > |s|` leaves the string unchanged; all-identical strings may collapse in waves.
