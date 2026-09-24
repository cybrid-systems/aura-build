from __future__ import annotations

# ListNode and helpers are provided by the harness, but we define them here for self-containedness.
class ListNode:
    __slots__ = ('val', 'next')

    def __init__(self, val: int = 0, next: 'ListNode | None' = None):
        self.val = val
        self.next = next


def solve(head: ListNode | None) -> bool:
    if head is None or head.next is None:
        return True

    # Step 1: Find the middle using slow/fast pointers.
    slow, fast = head, head
    while fast.next is not None and fast.next.next is not None:
        slow = slow.next
        fast = fast.next.next

    # Step 2: Reverse the second half starting at slow.next.
    second = _reverse(slow.next)

    # Step 3: Compare the two halves.
    p1, p2 = head, second
    result = True
    while p2 is not None:
        if p1.val != p2.val:
            result = False
            break
        p1 = p1.next
        p2 = p2.next

    # Step 4: Restore the list by reversing the second half back.
    slow.next = _reverse(second)

    return result


def _reverse(node: ListNode | None) -> ListNode | None:
    prev = None
    cur = node
    while cur is not None:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


def _build(values: list[int]) -> ListNode | None:
    if not values:
        return None
    head = ListNode(values[0])
    cur = head
    for v in values[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


CASES = [
    {"name": "odd_palindrome", "values": [1, 2, 3, 2, 1]},
    {"name": "non_palindrome", "values": [1, 2, 3]},
    {"name": "single_node", "values": [7]},
    {"name": "two_same", "values": [1, 1]},
    {"name": "two_diff", "values": [1, 2]},
    {"name": "even_palindrome", "values": [1, 2, 2, 1]},
    {"name": "longer_palindrome", "values": [1, 2, 3, 4, 3, 2, 1]},
    {"name": "longer_non_palindrome", "values": [1, 2, 3, 4, 5, 2, 1]},
]


if __name__ == '__main__':
    import json

    out = []
    for i, case in enumerate(CASES):
        head = _build(case["values"])
        result = solve(head)
        out.append({
            "id": i,
            "input": {"values": case["values"]},
            "expected": json.dumps(result, ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
