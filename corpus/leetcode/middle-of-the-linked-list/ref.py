import sys, json

class ListNode:
    __slots__ = ('val', 'next')
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def build_list(values):
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

def middle_node(head):
    slow = head
    fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
    return slow

def solve(head):
    if head is None:
        return None
    return middle_node(head)

CASES = [
    {"values": []},
    {"values": [1]},
    {"values": [1, 2]},
    {"values": [1, 2, 3]},
    {"values": [1, 2, 3, 4]},
    {"values": [1, 2, 3, 4, 5]},
    {"values": [10, 20, 30, 40, 50, 60, 70, 80]},
    {"values": [-1, 0, 1, 2, 3]},
]

if __name__ == '__main__':
    results = []
    for i, c in enumerate(CASES):
        head = build_list(c["values"])
        mid = solve(head)
        if mid is None:
            expected_str = ""
        else:
            expected_str = str(mid.val)
        results.append({
            "id": i,
            "input": {"values": c["values"]},
            "expected": expected_str
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
