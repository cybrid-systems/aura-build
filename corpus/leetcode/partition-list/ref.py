import json

class Node:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def build_list(values):
    if not values:
        return None
    head = Node(values[0])
    cur = head
    for v in values[1:]:
        cur.next = Node(v)
        cur = cur.next
    return head

def list_to_values(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out

def solve(head, x):
    if head is None:
        return None
    less_dummy = Node(0)
    ge_dummy = Node(0)
    less_tail = less_dummy
    ge_tail = ge_dummy
    cur = head
    while cur:
        if cur.val < x:
            less_tail.next = cur
            less_tail = cur
        else:
            ge_tail.next = cur
            ge_tail = cur
        cur = cur.next
    ge_tail.next = None
    less_tail.next = ge_dummy.next
    return less_dummy.next

def solve_wrapped(args):
    values, x = args
    head = build_list(values)
    result = solve(head, x)
    return list_to_values(result)

CASES = [
    {"args": ([1, 4, 3, 2, 5, 2], 3)},
    {"args": ([2, 1], 2)},
    {"args": ([], 1)},
    {"args": ([1], 1)},
    {"args": ([5, 4, 3, 2, 1], 3)},
    {"args": ([1, 2, 3, 4, 5], 10)},
    {"args": ([5, 4, 3, 2, 1], 0)},
    {"args": ([3, 1, 2, 4, 1], 3)},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve_wrapped(case["args"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
