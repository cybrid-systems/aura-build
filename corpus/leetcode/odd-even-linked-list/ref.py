from __future__ import annotations
import json
import sys
from typing import Optional


class Node:
    __slots__ = ("val", "next")

    def __init__(self, val: int = 0, next: Optional["Node"] = None) -> None:
        self.val = val
        self.next = next


def solve(head: Optional[Node]) -> Optional[Node]:
    if head is None or head.next is None:
        return head
    odd_head: Optional[Node] = head
    even_head: Optional[Node] = head.next
    odd_tail: Optional[Node] = odd_head
    even_tail: Optional[Node] = even_head
    cur: Optional[Node] = even_head.next
    is_odd: bool = True
    while cur is not None:
        nxt: Optional[Node] = cur.next
        if is_odd:
            assert odd_tail is not None
            odd_tail.next = cur
            odd_tail = cur
            odd_tail.next = None
        else:
            assert even_tail is not None
            even_tail.next = cur
            even_tail = cur
            even_tail.next = None
        cur = nxt
        is_odd = not is_odd
    assert odd_tail is not None
    odd_tail.next = even_head
    return odd_head


def build_list(values):
    if not values:
        return None
    head = Node(values[0])
    cur = head
    for v in values[1:]:
        cur.next = Node(v)
        cur = cur.next
    return head


def to_pylist(head):
    out = []
    cur = head
    seen = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        out.append(cur.val)
        cur = cur.next
    return out


CASES = [
    {"values": [1, 2, 3, 4, 5]},
    {"values": [2, 1, 3, 5, 6, 4, 7]},
    {"values": [1]},
    {"values": [1, 2]},
    {"values": [1, 2, 3]},
    {"values": [10, 20, 30, 40, 50, 60]},
    {"values": [7, 7, 7, 7]},
    {"values": [-1, -2, -3, -4, -5, -6, -7, -8]},
]


if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        values = case["values"]
        head = build_list(values)
        new_head = solve(head)
        out_values = to_pylist(new_head)
        results.append({
            "id": i,
            "input": {"values": values},
            "expected": json.dumps(out_values, separators=(',', ':'), ensure_ascii=False),
        })
    sys.stdout.write(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
    sys.stdout.write("\n")
