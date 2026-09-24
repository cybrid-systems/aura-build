# Keys and Rooms

## Problem

You are given `N` rooms numbered `0` to `N-1`. Room `0` is unlocked; all other rooms are locked.

Each room `i` contains a list of distinct keys, where each key is the index of another room that the key unlocks. When you visit a room, you collect all keys inside it and can immediately use them to unlock other rooms.

Starting from room `0`, determine whether it is possible to visit **every** room.

## Input

The input is provided on standard input.

The first line contains an integer `N` — the number of rooms.

The next `N` lines each describe one room. The `i`-th line starts with an integer `k_i` (the number of keys in room `i`), followed by `k_i` integers representing the rooms those keys unlock.

```
N
k_0 a_0_1 a_0_2 ... a_0_k0
k_1 a_1_1 a_1_2 ... a_1_k1
...
k_{N-1} a_{N-1}_1 ... a_{N-1}_{k_{N-1}}
```

### Convention (Aura harness)

The harness exposes a single call:

```
solve(case_id: int) -> str
```

For each `CASE0` line in the embedded cases, your `solve` function will be invoked. The expected output for each case is the string `"True"` if all rooms are reachable, otherwise `"False"` (case-sensitive). Each result is printed on its own line in case order.

## Function Signature

```python
def solve(case_id: int) -> str:
    # case_id identifies which test case is being solved.
    # Return "True" if all rooms can be visited, else "False".
    ...
```

## Output Format

Print one line per case:

```
True
```

or

```
False
```

depending on whether all rooms are reachable starting from room `0`.

## Constraints

- `1 ≤ N ≤ 1000`
- `0 ≤ k_i ≤ N`
- Keys within a single room are distinct.
- `0 ≤ a_i_j < N`

## Example

**Input (as a `CASE0` line):**

```
CASE0=3 | 3 | 3 1 2 0 1 0 0
```

Decoded:
- `N = 3`
- Room `0` has keys `[1, 2]`
- Room `1` has key `[0]`
- Room `2` has no keys

**Output:**

```
True
```

All three rooms are reachable from room `0`.

## Notes

- Use DFS or BFS starting from room `0`, tracking which rooms have been visited. If the count of visited rooms equals `N`, output `"True"`; otherwise `"False"`.
- The `"True"`/`"False"` output must be exact strings, not `1`/`0` or `YES`/`NO`.
