from __future__ import annotations
from typing import Optional

class ListNode:
    __slots__ = ("val", "next")
    def __init__(self, val: int = 0, next: Optional["ListNode"] = None):
        self.val = val
        self.next = next

def _build(values):
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = tail = node
        else:
            tail.next = node
            tail = node
    return head

def _to_list(node):
    out = []
    while node is not None:
        out.append(node.val)
        node = node.next
    return out

def solve(head: Optional[ListNode], k: int) -> list[Optional[ListNode]]:
    # Determine length
    n = 0
    cur = head
    while cur is not None:
        n += 1
        cur = cur.next

    base = n // k
    extra = n % k  # first `extra` parts get one extra node

    parts: list[Optional[ListNode]] = []
    cur = head
    for i in range(k):
        size = base + (1 if i < extra else 0)
        part_head = cur
        # Advance `size - 1` links, then cut.
        prev = None
        for _ in range(size):
            if cur is not None:
                prev = cur
                cur = cur.next
        # Cut: prev is the last node of this part
        if prev is not None:
            prev.next = None
        parts.append(part_head)

    return parts

CASES = [
    {"head": [1,2,3,4,5,6,7,8,9,10], "k": 3},
    {"head": [1,2,3,4,5], "k": 5},
    {"head": [], "k": 3},
    {"head": [1,2,3], "k": 5},
    {"head": [1,2,3,4,5,6,7,8], "k": 4},
    {"head": [1], "k": 1},
    {"head": [1,2,3,4,5,6,7], "k": 3},
    {"head": list(range(1, 21)), "k": 4},
]

if __name__ == "__main__":
    import json
    out = []
    for i, c in enumerate(CASES):
        h = _build(c["head"])
        parts = solve(h, c["k"])
        # canonicalize: convert each part's linked list to a Python list
        canonical_parts = [_to_list(p) for p in parts]
        out.append({"id": i, "input": c, "expected": json.dumps(canonical_parts, separators=(",", ":"), ensure_ascii=False)})
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
