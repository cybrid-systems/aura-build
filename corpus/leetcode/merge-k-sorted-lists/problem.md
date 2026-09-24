# Merge k Sorted Lists

## Problem

You are given `k` sorted singly linked lists. Merge them into a single sorted linked list and return its head.

Each list node has an integer value `val` and a pointer to the next node. The input lists are already sorted in non-decreasing order, and the total number of nodes across all lists is at most `10^4`.

Your solution should run in `O(N log k)` time, where `N` is the total number of nodes across all lists and `k` is the number of lists.

## Function Signature

```clojure
(solve lists)
```

- `lists` is a vector of `k` linked lists. Each linked list is represented as a vector of integers, where the first element is the value of the head node, followed by the values of subsequent nodes in order. An empty list (`[]`) represents `nil` (no nodes).
- Returns a single linked list in the same vector-of-integers representation, sorted in non-decreasing order. If all input lists are empty, return `[]`.

## Input

The input is provided as a single line:

```
CASE0=[[1,4,5],[1,3,4],[2,6]]
```

The format is `CASE0=<value>`, where `<value>` is the JSON-encoded value of the `lists` argument.

## Output

Print the merged linked list as a JSON-encoded vector of integers on a single line:

```
[1,1,2,3,4,4,5,6]
```

## Notes

- Use a min-heap (priority queue) of size `k` to efficiently select the smallest head node at each step. This gives the required `O(N log k)` complexity.
- For `k == 0` (empty input vector) or when all lists are empty, the result is `[]`.
