# Bitwise XOR of All Pairings

You are given three integer arrays. The first array has `n` elements, the second has `m` elements, and the third has `k` elements.

Consider all `n * m` ordered pairs `(i, j)` formed by taking one element from the first array and one from the second array. For each such pair, we define the **pairing value** as the bitwise XOR of the two selected elements, XORed again with a value taken from the third array. More precisely, for each pair `(i, j)`, the pairing value is:

```
pairing_value(i, j) = arr1[i] XOR arr2[j] XOR arr3[?]    (each pairing uses some element of arr3)
```

However, due to the properties of the XOR operation, we do not actually need to enumerate every pair. Instead, observe that:

- If an array has **even size**, then XORing all its elements together yields `0`, which means each element from the other array effectively contributes `0` to the final pairing sum and can be ignored.
- If an array has **odd size**, then XORing all its elements yields the XOR of its distinct elements, and each element of this array contributes to every pairing with every element of the other arrays.

## Task

Given the three arrays, compute the bitwise XOR of all pairing values as defined above.

## Function Signature

```clojure
(solve arr1 arr2 arr3)
```

- `arr1`, `arr2`, `arr3` : vectors of integers.
- Returns a single integer: the XOR of all pairing values.

## Input Format

The input is provided in the standard `CASE0=...` format:

```
CASE0=[v1 v2 ... vn]
CASE1=[u1 u2 ... um]
CASE2=[w1 w2 ... wk]
```

Each line after `CASE0=` contains a sequence of integers representing an array. The values are non-negative integers.

## Output Format

A single integer printed to stdout, representing the XOR of all pairing values.

## Examples

**Example 1**
```
CASE0=[1 2 3]
CASE1=[4 5]
CASE2=[6]
```
Output: `0`

Explanation: `arr2` has size 2 (even), so it contributes `0`. The pairing reduces to `(arr1[i] XOR 6)` for each `i`, then XORed together. Since `arr1` has odd size 3, we XOR `arr1[0] XOR 6`, `arr1[1] XOR 6`, `arr1[2] XOR 6`. Each `6` appears an odd number of times? Actually 3 times (odd), so they cancel. The remaining XOR is `1 XOR 2 XOR 3 = 0`. Final answer: `0`.

**Example 2**
```
CASE0=[12 15]
CASE1=[5 7 9 11]
CASE2=[2 4 6 8 10]
```
Output: `8`

## Constraints

- `0 <= n, m, k <= 10^5`
- Each element fits in a 32-bit unsigned integer.

## Notes

- Use the parity property of XOR: an element appears in the final result if and only if the **combined multiplier** (the product of sizes of the other arrays) is odd.
- Time complexity should be `O(n + m + k)` in the worst case.
- Remember that `XOR` of an empty array is `0`.
