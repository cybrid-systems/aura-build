import json
from typing import Optional, List


class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next


def list_to_nodes(digits: List[int]) -> Optional[ListNode]:
    head = None
    cur = None
    for d in digits:
        node = ListNode(d)
        if head is None:
            head = node
            cur = node
        else:
            cur.next = node
            cur = node
    return head


def nodes_to_list(node: Optional[ListNode]) -> List[int]:
    out = []
    while node is not None:
        out.append(node.val)
        node = node.next
    return out


def solve(l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
    dummy = ListNode(0)
    tail = dummy
    carry = 0
    a, b = l1, l2
    while a is not None or b is not None or carry != 0:
        s = carry
        if a is not None:
            s += a.val
            a = a.next
        if b is not None:
            s += b.val
            b = b.next
        carry, digit = divmod(s, 10)
        tail.next = ListNode(digit)
        tail = tail.next
    return dummy.next


CASES = [
    {"l1": [2, 4, 3], "l2": [5, 6, 4]},
    {"l1": [0], "l2": [0]},
    {"l1": [9, 9, 9, 9], "l2": [9, 9, 9, 9, 9, 9]},
    {"l1": [1], "l2": [9, 9]},
    {"l1": [5], "l2": [5]},
    {"l1": [1, 2, 3], "l2": [4, 5, 6]},
    {"l1": [9], "l2": [1, 9, 9]},
    {"l1": [2, 4, 3, 9, 9], "l2": [5, 6, 4]},
]


if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        l1 = list_to_nodes(case["l1"])
        l2 = list_to_nodes(case["l2"])
        result_nodes = solve(l1, l2)
        result_list = nodes_to_list(result_nodes)
        results.append({
            "id": idx,
            "input": {"l1": case["l1"], "l2": case["l2"]},
            "expected": json.dumps(result_list, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
