class Node:
    def __init__(self, value: int, next: 'Node | None' = None):
        self.value = value
        self.next = next


def solve(head: Node | None) -> Node | None:
    prev = None
    curr = head
    while curr is not None:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev


# Helpers for building/serializing lists and running cases
def build(values):
    dummy = Node(0)
    cur = dummy
    for v in values:
        cur.next = Node(v)
        cur = cur.next
    return dummy.next


def to_list(node):
    out = []
    while node is not None:
        out.append(node.value)
        node = node.next
    return out


CASES = [
    {"head": build([])},
    {"head": build([1])},
    {"head": build([1, 2, 3, 4, 5])},
    {"head": build([1, 2])},
    {"head": build([7, 7, 7, 7])},
    {"head": build([-3, -2, -1, 0, 1, 2])},
    {"head": build([100])},
    {"head": build([1, 2, 3])},
]


if __name__ == '__main__':
    import json

    results = []
    for i, case in enumerate(CASES):
        result = solve(case["head"])
        expected_canon = to_list(result)
        results.append({
            "id": i,
            "input": {"head": to_list(case["head"])},
            "expected": json.dumps(expected_canon, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
