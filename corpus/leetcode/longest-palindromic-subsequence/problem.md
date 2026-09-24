# Longest Palindromic Subsequence

Given a string `s`, find the length of the longest **subsequence** of `s` that is a palindrome.

A subsequence is obtained by deleting zero or more characters without reordering the remaining ones. For example, from `"BBABCBCAB"` one of the longest palindromic subsequences is `"BABCBAB"` with length 7.

## Input

A single line containing the string `s`.

- `1 ≤ |s| ≤ 1000`
- `s` consists of printable ASCII characters (treat each character as a single unit).

## Output

Print a single integer: the length of the longest palindromic subsequence of `s`.

## Example

```
Input:
BBABCBCAB

Output:
7
```

## Notes

- The empty subsequence counts as a palindrome of length 0, so the answer is always at least 0.
- Standard DP approach: `dp[i][j]` = longest palindromic subsequence length in `s[i..j]`. Recurrence:
  - If `s[i] == s[j]` and `i != j`: `dp[i][j] = dp[i+1][j-1] + 2`; if `i == j`: `dp[i][j] = 1`.
  - Else: `dp[i][j] = max(dp[i+1][j], dp[i][j-1])`.
- Fill the table in order of increasing substring length. Answer is `dp[0][n-1]`.

## Function Signature (hint)

```
def solve(s: str) -> int
```

The harness will read the single string from standard input, call `solve(s)`, and compare the returned integer against the expected answer.
