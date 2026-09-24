# Sort List

**Category:** linked_list

## Statement

Given the head of a singly linked list, return the list with its nodes sorted in ascending order by value.

Requirements:
- **Time complexity:** `O(n log n)`
- **Space complexity:** `O(1)` (not counting recursion stack / output list)

The list will contain between 0 and 10⁵ nodes, with values in the range `[-10⁵, 10⁵]`.

## Function Signature

```clojure
(solve head) ; => sorted-head
```

- `head` — a list/sequence representing the linked list (first element is the head).
- Returns a list/sequence representing the sorted linked list.

## Input / Output Convention

The harness runs the function directly with no stdin. Cases are encoded as `CASE0=...` style bindings exposed in the REPL/eval environment; for example:

```
CASE0_input  = [4 2 1 3]
CASE0_output = [1 2 3 4]

CASE1_input  = [-1 5 3 4 0]
CASE1_output = [-1 0 3 4 5]

CASE2_input  = []
CASE2_output = []
```

The `solve` implementation receives the input list and must return the corresponding output list.

## Notes

- A standard `O(n log n)` approach is top-down or bottom-up **merge sort** on the linked list, exploiting `O(1)` extra space by rearranging pointers rather than allocating arrays.
- Remember to handle edge cases: empty list and single-node list.
- Use a **slow/fast pointer** technique to find the middle for splitting (top-down variant), or iteratively merge sublists of doubling length (bottom-up variant, true `O(1)` auxiliary space).
