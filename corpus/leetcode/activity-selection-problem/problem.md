# Activity Selection Problem

## Problem Statement

You are given a set of activities, each with a start time and an end time. Two activities are considered compatible if they do not overlap in time (an activity that ends exactly at the time another starts is allowed). Your task is to select the maximum number of compatible activities from the given set.

## Input Format

The input is read from standard input using the `CASE0=...` convention. The first line contains an integer `n`, the number of activities. The next `n` lines each contain two integers `s_i` and `e_i`, representing the start and end times of activity `i`.

```
CASE0=4
CASE1=1 3
CASE2=2 5
CASE3=4 7
CASE4=6 9
```

## Output Format

Print the maximum number of non-overlapping activities that can be selected.

```
3
```

## Function Signature

```clojure
(defn solve []
  ;; read from *in*, write to *out*
  )
```

## Constraints

- `1 <= n <= 1000`
- `0 <= s_i < e_i <= 10^9`

## Notes

- Activities with the same end time can be ordered arbitrarily; pick by start time as a tie-breaker.
- An activity ending at time `t` is compatible with another starting at time `t`.
