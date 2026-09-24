import sys
import json
from typing import Optional


class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next


def solve(head: Optional[ListNode]) -> Optional[ListNode]:
    dummy = ListNode(0, head)
    prev = dummy
    curr = head
    while curr:
        # If current value has duplicates, skip them all
        if curr.next and curr.next.val == curr.val:
            dup_val = curr.val
            while curr and curr.val == dup_val:
                nxt = curr.next
                curr.next = None
                curr = nxt
            prev.next = curr
        else:
            prev = curr
            curr = curr.next
    return dummy.next


def list_to_linked(values):
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head


def linked_to_list(node):
    result = []
    while node:
        result.append(node.val)
        node = node.next
    return result


def parse_input(data):
    lines = data.strip().split('\n')
    # Expect CASE0, n, values..., END
    idx = 0
    if lines[idx].strip() != 'CASE0':
        idx += 1
    idx += 1  # skip CASE0
    n = int(lines[idx].strip())
    idx += 1
    if n == 0:
        values = []
    else:
        values = list(map(int, lines[idx].strip().split()))
        idx += 1
    # skip END
    return values


CASES = [
    {"values": [1, 2, 3, 3, 4, 4, 5, 6]},
    {"values": [1, 1, 1, 2, 3]},
    {"values": []},
    {"values": [1, 2, 3]},
    {"values": [1, 1, 2, 2, 3, 3]},
    {"values": [1]},
    {"values": [1, 2, 2, 3, 3, 3, 4, 5, 5]},
    {"values": [-1, -1, 0, 0, 1, 2, 2]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        values = case["values"]
        head = list_to_linked(values)
        result_head = solve(head)
        result_values = linked_to_list(result_head)
        results.append({
            "id": i,
            "input": {"values": values},
            "expected": json.dumps(result_values, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
