class Node:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def solve(head):
    result = 0
    curr = head
    while curr:
        result = result * 2 + curr.val
        curr = curr.next
    return result

def build_linked_list(values):
    if not values:
        return None
    head = Node(values[0])
    curr = head
    for v in values[1:]:
        curr.next = Node(v)
        curr = curr.next
    return head

def linked_list_to_list(head):
    out = []
    curr = head
    while curr:
        out.append(curr.val)
        curr = curr.next
    return out

CASES = [
    {"values": [1]},
    {"values": [0]},
    {"values": [1, 0, 1]},
    {"values": [1, 1, 1, 1, 1]},
    {"values": [0, 0, 0, 0, 0]},
    {"values": [1, 0, 0, 1, 0, 1, 0]},
    {"values": [1] * 30},
    {"values": [0] + [1] * 29},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        head = build_linked_list(case["values"])
        result = solve(head)
        results.append({
            "id": i,
            "input": {"values": case["values"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
