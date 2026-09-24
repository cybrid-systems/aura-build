## Convert Binary Number in a Linked List to Integer

### Problem Statement

Given a singly linked list where each node contains a single digit (either `0` or `1`), the digits together represent a binary number. The most significant digit is at the head of the list. Convert this binary representation into its decimal integer equivalent.

For example, the list `1 -> 0 -> 1` represents the binary number `101`, which equals `5` in decimal.

### Function Signature

```python
def solve(head):
    ...
```

Where `head` is the head node of a linked list. Each node has the following structure:

```python
class Node:
    def __init__(self, val=0, next=None):
        self.val = val      # int: 0 or 1
        self.next = next    # Node or None
```

The function should return an integer — the decimal value of the binary number.

### Input / Output Convention

The harness feeds a single case via standard input in the following format:

```
CASE0=<count>
N0_0=<value>
N0_1=<value>
...
```

Here:
- `CASE0=5` means the linked list has **5** nodes.
- `N0_0`, `N0_1`, ... are the values of the nodes from head to tail (each is `0` or `1`).

The function should print the decimal integer to standard output.

### Notes

- The linked list contains only digits `0` and `1`.
- The list length is between 1 and 30, so the result fits comfortably in a 32-bit integer.
- You may not have access to the length ahead of time — traverse the list as you would in a standard interview setting.
- An efficient approach reads each digit once, accumulating the result as `result = result * 2 + digit`.
