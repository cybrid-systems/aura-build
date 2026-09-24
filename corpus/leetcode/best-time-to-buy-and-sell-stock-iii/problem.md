# Best Time to Buy and Sell Stock III

## Statement

You are given an array `prices` where `prices[i]` is the price of a given stock on day `i`.

You may complete **at most two** transactions (buy one and sell one share of the stock). A transaction consists of buying a share on one day and selling it on a **later** day. The two transactions must **not overlap** (you must sell the first share before buying the second).

Design and implement an algorithm to find the **maximum profit** you can achieve. Return `0` if no profit is possible.

## Function Signature

```clojure
(solve prices)
```

- `prices` — a vector of integers (the price sequence).
- Returns the maximum achievable profit as a long/integer.

## Input / Output Convention

The harness is **stdin-less**; `solve` is called directly by the Aura runner. When a reference checker is wired, input/output is provided via these leading lines for transparency:

```
CASE0=vector<Long> prices
CASE0.ANS=<long>
```

`CASE0.ANS` is the expected output for the sample case. Your implementation should match the documented behavior on this case and the hidden cases used by the grader.

## Notes

- The two transactions are independent in *direction* but must be sequential in time: first buy/sell finishes before the second buy/sell starts.
- A single transaction (or zero transactions) is a valid answer when it yields the maximum profit — you are not required to use two.
- The expected complexity is **O(n)** time and **O(n)** or **O(1)** auxiliary space; an **O(n²)** brute force will likely time out on large inputs.
