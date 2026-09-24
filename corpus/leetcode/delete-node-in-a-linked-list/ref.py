import json

class Node:
    __slots__ = ('val', 'next')
    def __init__(self, val, nxt=None):
        self.val = val
        self.next = nxt

def build_list(values):
    if not values:
        return None
    head = Node(values[0])
    cur = head
    for v in values[1:]:
        cur.next = Node(v)
        cur = cur.next
    return head

def get_node(head, index):
    cur = head
    for _ in range(index):
        cur = cur.next
    return cur

def list_from_node(node):
    out = []
    while node is not None:
        out.append(node.val)
        node = node.next
    return out

def solve(node):
    # Copy next node's value into this node, then skip the next node
    nxt = node.next
    node.val = nxt.val
    node.next = nxt.next

CASES = [
    {"id": 0, "values": [4, 5, 1, 9], "index": 1},
    {"id": 1, "values": [1, 2, 3, 4, 5], "index": 0},
    {"id": 2, "values": [1, 2, 3, 4, 5], "index": 3},
    {"id": 3, "values": [7, 8], "index": 0},
    {"id": 4, "values": [10, 20, 30], "index": 1},
    {"id": 5, "values": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "index": 4},
    {"id": 6, "values": [42, -1, 0, 99], "index": 2},
    {"id": 7, "values": [1, 2], "index": 0},
]

if __name__ == '__main__':
    results = []
    for case in CASES:
        head = build_list(case["values"])
        target = get_node(head, case["index"])
        solve(target)
        result_list = list_from_node(head)
        expected = " ".join(str(x) for x in result_list)
        results.append({
            "id": case["id"],
            "input": {
                "values": case["values"],
                "index": case["index"]
            },
            "expected": json.dumps(result_list, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
