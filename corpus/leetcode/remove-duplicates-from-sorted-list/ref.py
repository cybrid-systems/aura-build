import json
from typing import Optional


class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next


def build_list(vals):
    head = None
    tail = None
    for v in vals:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head


def to_list(head):
    out = []
    cur = head
    while cur is not None:
        out.append(cur.val)
        cur = cur.next
    return out


def solve(head: Optional[ListNode]) -> Optional[ListNode]:
    if head is None:
        return None
    cur = head
    while cur is not None and cur.next is not None:
        if cur.next.val == cur.val:
            cur.next = cur.next.next
        else:
            cur = cur.next
    return head


CASES = [
    {"N": 5, "vals": [1, 1, 2, 3, 3]},
    {"N": 1, "vals": [1]},
    {"N": 0, "vals": []},
    {"N": 7, "vals": [1, 1, 1, 1, 2, 3, 3]},
    {"N": 6, "vals": [1, 2, 3, 4, 5, 6]},
    {"N": 4, "vals": [1, 1, 1, 1]},
    {"N": 5, "vals": [1, 2, 2, 2, 3]},
    {"N": 3, "vals": [0, 0, 0]},
]


def main():
    results = []
    for i, case in enumerate(CASES):
        head = build_list(case["vals"])
        new_head = solve(head)
        out_vals = to_list(new_head)
        results.append({
            "id": i,
            "input": {"N": case["N"], "vals": case["vals"]},
            "expected": json.dumps(out_vals, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))


if __name__ == '__main__':
    main()
