class Node:
    __slots__ = ('val', 'next')
    def __init__(self, val, nxt=None):
        self.val = val
        self.next = nxt

def build_list(values):
    head = None
    tail = None
    for v in values:
        node = Node(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head

def insertion_sort(head):
    sorted_head = None
    cur = head
    while cur is not None:
        nxt = cur.next
        # Find insertion point in sorted list
        # Find the node after which to insert (prev) and where cur goes
        # Special case: insert at head
        if sorted_head is None or cur.val < sorted_head.val:
            cur.next = sorted_head
            sorted_head = cur
        else:
            # Find the right place
            prev = sorted_head
            while prev.next is not None and prev.next.val < cur.val:
                prev = prev.next
            cur.next = prev.next
            prev.next = cur
        cur = nxt
    return sorted_head

def list_to_vec(head):
    result = []
    cur = head
    while cur is not None:
        result.append(cur.val)
        cur = cur.next
    return result

def solve(N, VALUES):
    head = build_list(VALUES)
    sorted_head = insertion_sort(head)
    return list_to_vec(sorted_head)

CASES = [
    {"N": 0, "VALUES": []},
    {"N": 1, "VALUES": [5]},
    {"N": 5, "VALUES": [4, 2, 1, 3, 5]},
    {"N": 6, "VALUES": [-1, 5, 3, 4, 0, 2]},
    {"N": 7, "VALUES": [3, 3, 1, 2, 2, 1, 3]},
    {"N": 3, "VALUES": [1, 2, 3]},
    {"N": 3, "VALUES": [3, 2, 1]},
    {"N": 8, "VALUES": [-5, 10, -3, 8, 8, 0, 1, -5]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["N"], case["VALUES"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
