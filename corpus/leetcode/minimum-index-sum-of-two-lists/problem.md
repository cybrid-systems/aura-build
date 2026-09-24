# Minimum Index Sum of Two Lists

Given two lists of strings `list1` and `list2`, find all common strings that appear in both lists, and among those, return the ones whose **sum of indices** (index in `list1` + index in `list2`) is the smallest.

If multiple strings share this minimum index sum, return **all of them**. The order of the result does not matter.

## Function Signature

```lisp
(solve list1 list2)
```

- `list1`, `list2` : lists of distinct strings
- returns : a list of strings (common strings with the smallest index sum)

## Input Convention (CASE0)

The harness feeds the problem via `CASE0` lines instead of stdin:

```
CASE0=list1=["Shogun","Tapioca Express","Burger King","KFC"]
CASE0=list2=["Piatti","The Grill at Torrey Pines","Hungry Hunter Steakhouse","Shogun"]
```

- One `CASE0=key=value` line per parameter.
- Values use JSON-like array literals; strings are double-quoted.
- Lines appear in the order the function parameters are declared.

## Examples

**Example 1**
```
list1 = ["Shogun","Tapioca Express","Burger King","KFC"]
list2 = ["Piatti","The Grill at Torrey Pines","Hungry Hunter Steakhouse","Shogun"]
```
Common string `"Shogun"` has index sum `0 + 3 = 3`.  
Output → `["Shogun"]`

**Example 2**
```
list1 = ["Shogun","Tapioca Express","Burger King","KFC"]
list2 = ["KFC","Shogun","Burger King"]
```
- `"Shogun"` → `0 + 1 = 1`
- `"Burger King"` → `2 + 2 = 4`
- `"KFC"` → `3 + 0 = 3`

Minimum sum is `1`.  
Output → `["Shogun"]`

**Example 3**
```
list1 = ["Shogun","Tapioca Express","Burger King","KFC"]
list2 = ["Tapioca Express","Shogun","Burger King","KFC"]
```
- `"Tapioca Express"` → `1 + 0 = 1`
- `"Shogun"` → `0 + 1 = 1`
- `"Burger King"` → `2 + 2 = 4`
- `"KFC"` → `3 + 3 = 6`

Minimum sum is `1`, shared by two strings.  
Output → `["Shogun","Tapioca Express"]` (order does not matter)

## Notes

- Each input list contains only **distinct** strings (no duplicates within a single list).
- An efficient approach uses a hash map from string → its index in `list1`, then a single pass over `list2` to compute candidate sums in O(n + m).
- The output list may contain 1 or more strings; preserve all ties at the minimum sum.
