# Koko Eating Bananas

Koko loves to eat bananas. There are `n` piles of bananas, where the `i`-th pile has `piles[i]` bananas. The guards have gone and will come back in `h` hours.

Koko can decide her bananas-per-hour eating speed `k`. Each hour, she chooses a pile and eats `k` bananas from that pile. If the pile has fewer than `k` bananas, she eats the whole pile and won't eat any other pile during that hour.

Return the minimum integer `k` such that she can eat all the bananas within `h` hours.

## Function Signature

```python
def solve(piles: list[int], h: int) -> int:
    ...
```

## Input / Output Convention

The harness reads test cases from a single text stream using the following format:

- The first line is the integer `CASE` = number of test cases.
- Each test case is given as two lines:
  1. Two integers `n h` (number of piles, available hours).
  2. `n` space-separated integers `piles[0] .. piles[n-1]`.

For example:

```
CASE0=2
2 4
3 1
3 6
1 2 3
```

Means: 2 test cases.
- Case 0: `n=2, h=4, piles=[3,1]` → Koko's minimum eating speed is `4` (eats 3 + 1 in 2 hours).
- Case 1: `n=3, h=6, piles=[1,2,3]` → minimum speed is `2`.

The `solve` function receives the already-parsed inputs and should return the integer answer.

## Notes

- `1 <= piles[i] <= 10^9`, `1 <= n <= 10^5`, `piles.length <= h <= 10^9`. The answer always fits in 64-bit.
- A pile of size `p` eaten at speed `k` takes `ceil(p / k)` hours.
- Think binary search on the eating speed `k` over `[1, max(piles)]`.
