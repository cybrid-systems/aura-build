import sys
import json
from typing import List, Optional

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def build_list(s: str) -> Optional[ListNode]:
    if s.strip() in ('', 'None'):
        return None
    vals = [int(x) for x in s.strip().split('->')]
    head = ListNode(vals[0])
    cur = head
    for v in vals[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head

def list_to_str(head: Optional[ListNode]) -> str:
    parts = []
    cur = head
    while cur:
        parts.append(str(cur.val))
        cur = cur.next
    return '->'.join(parts)

def reverse_k_group(head: Optional[ListNode], k: int) -> Optional[ListNode]:
    if head is None or k <= 1:
        return head
    # Find length first to determine how many groups
    length = 0
    cur = head
    while cur:
        length += 1
        cur = cur.next
    full_groups = length // k
    if full_groups == 0:
        return head
    dummy = ListNode(0)
    dummy.next = head
    prev_group_end = dummy
    cur = head
    for _ in range(full_groups):
        # cur is start of group, reverse k nodes
        prev = None
        nxt = cur.next
        for _i in range(k):
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        # prev is new head of group, cur is next group's start (or None)
        group_new_head = prev
        prev_group_end.next = group_new_head
        # advance prev_group_end to end of just-reversed group (= old cur group start... actually old "head" of group)
        prev_group_end = head  # this was original head before reversal; after reversal it is last of the group
        head = cur  # for next iteration, but we use prev_group_end.next = cur afterwards
        # wire end of reversed group to next segment
        prev_group_end.next = cur
    return dummy.next

def solve(head: ListNode, k: int) -> ListNode:
    return reverse_k_group(head, k)

def parse_stdin(text: str):
    cases = []
    lines = text.splitlines()
    for line in lines:
        line = line.rstrip('\n')
        if not line:
            continue
        if line.startswith('CASE') and '_K=' in line:
            idx_part = line.split('CASE')[1].split('_K=')
            idx = int(idx_part[0])
            k = int(idx_part[1])
            cases.append((idx, None, k))
        elif line.startswith('CASE') and '=' in line:
            idx_part = line.split('CASE')[1].split('=', 1)
            idx = int(idx_part[0])
            val = idx_part[1]
            cases.append((idx, val, None))
    # Now pair
    by_idx = {}
    for idx, v, k in cases:
        by_idx.setdefault(idx, [None, None])
        if v is not None:
            by_idx[idx][0] = v
        else:
            by_idx[idx][1] = k
    ordered = []
    for i in sorted(by_idx.keys()):
        lst_str, k = by_idx[i]
        ordered.append((lst_str, k))
    return ordered

CASES = [
    # Edge cases and typical cases
    {"name": "k=1 no change", "list": "1->2->3->4->5", "k": 1},
    {"name": "single node", "list": "1", "k": 2},
    {"name": "k equals length", "list": "1->2->3", "k": 3},
    {"name": "k greater than length", "list": "1->2", "k": 5},
    {"name": "example 1", "list": "1->2->3->4->5", "k": 2},
    {"name": "example 2", "list": "1->2->3->4->5", "k": 3},
    {"name": "example 3", "list": "1->2->3->4->5->6->7->8", "k": 4},
    {"name": "negatives", "list": "-3->-1->2->-5->4", "k": 2},
]

def run_case(c):
    head = build_list(c["list"])
    new_head = solve(head, c["k"])
    return list_to_str(new_head)

if __name__ == '__main__':
    results = []
    for i, c in enumerate(CASES):
        out = run_case(c)
        results.append({"id": i, "input": {"list": c["list"], "k": c["k"]}, "expected": out})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
