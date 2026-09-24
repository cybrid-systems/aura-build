from typing import Optional, List, Union

class ListNode:
    def __init__(self, val: int, next: Optional['ListNode'] = None):
        self.val = val
        self.next = next

def _build(values: Union[List[int], None]) -> Optional[ListNode]:
    if not values:
        return None
    head = ListNode(values[0])
    cur = head
    for v in values[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head

def _to_list(node: Optional[ListNode]) -> List[int]:
    out = []
    while node:
        out.append(node.val)
        node = node.next
    return out

def reorder(head_arg) -> Optional[ListNode]:
    head = _build(head_arg) if not isinstance(head_arg, ListNode) and head_arg is not None else head_arg
    if head is None or head.next is None:
        return head
    # 1. find middle
    slow, fast = head, head
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    # 2. reverse second half
    prev, cur = None, slow.next
    slow.next = None
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    # 3. merge
    first, second = head, prev
    while second:
        t1, t2 = first.next, second.next
        first.next = second
        second.next = t1
        first, second = t1, t2
    return head

def solve(head_arg) -> Union[Optional[ListNode], List[int]]:
    new_head = reorder(head_arg)
    return _to_list(new_head)

CASES = [
    {"head": []},
    {"head": [1]},
    {"head": [1, 2]},
    {"head": [1, 2, 3, 4]},
    {"head": [1, 2, 3, 4, 5]},
    {"head": [1, 2, 3, 4, 5, 6]},
    {"head": [1, 2, 3, 4, 5, 6, 7]},
    {"head": [1, 2, 3, 4, 5, 6, 7, 8, 9]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["head"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
