from typing import List, Optional

class ListNode:
    def __init__(self, val: int = 0, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next

def build_list(values: List[int]) -> Optional[ListNode]:
    head = ListNode(0)
    cur = head
    for v in values:
        cur.next = ListNode(v)
        cur = cur.next
    return head.next

def list_to_values(head: Optional[ListNode]) -> List[int]:
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out

def solve(list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
    dummy = ListNode(0)
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next = list1
            list1 = list1.next
        else:
            tail.next = list2
            list2 = list2.next
        tail = tail.next
    tail.next = list1 if list1 else list2
    return dummy.next


CASES = [
    {"list1": [1, 2, 4], "list2": [1, 3, 4]},
    {"list1": [],       "list2": []},
    {"list1": [],       "list2": [0]},
    {"list1": [1],      "list2": [2]},
    {"list1": [2],      "list2": [1]},
    {"list1": [1, 3, 5, 7], "list2": [2, 4, 6, 8]},
    {"list1": [-3, -1, 2], "list2": [-2, 0, 1]},
    {"list1": [1, 2, 3], "list2": [1, 2, 3]},
]

if __name__ == '__main__':
    import json
    results = []
    for i, c in enumerate(CASES):
        l1 = build_list(c["list1"])
        l2 = build_list(c["list2"])
        merged = solve(l1, l2)
        vals = list_to_values(merged)
        expected = " ".join(str(v) for v in vals)
        results.append({
            "id": i,
            "input": {"list1": c["list1"], "list2": c["list2"]},
            "expected": expected,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
