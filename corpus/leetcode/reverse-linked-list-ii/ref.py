def solve(head, m, n):
    # sentinel dummy for m==1 handling
    dummy = Node(None)
    dummy.next = head
    pre = dummy
    for _ in range(m - 1):
        pre = pre.next
    cur = pre.next
    # reverse the (n-m) links in-place
    for _ in range(n - m):
        nxt = cur.next
        cur.next = nxt.next
        nxt.next = pre.next
        pre.next = nxt
    return dummy.next


class Node:
    __slots__ = ("val", "next")
    def __init__(self, val, nxt=None):
        self.val = val
        self.next = nxt


def build_list(values):
    dummy = Node(None)
    cur = dummy
    for v in values:
        cur.next = Node(v)
        cur = cur.next
    return dummy.next


def to_list(head):
    out = []
    cur = head
    seen = 0
    while cur is not None and seen < 1000:
        out.append(cur.val)
        cur = cur.next
        seen += 1
    return out


CASES = [
    {"head": [1,2,3,4,5], "m": 2, "n": 4},
    {"head": [1,2,3,4,5], "m": 1, "n": 5},
    {"head": [5], "m": 1, "n": 1},
    {"head": [1,2,3,4,5], "m": 3, "n": 3},
    {"head": [1,2,3,4,5], "m": 1, "n": 1},
    {"head": [1,2,3,4,5], "m": 4, "n": 5},
    {"head": [], "m": 1, "n": 1},
    {"head": [10,20,30,40,50,60,70], "m": 2, "n": 6},
]


if __name__ == '__main__':
    import json
    results = []
    for i, c in enumerate(CASES):
        h = build_list(c["head"])
        new_h = solve(h, c["m"], c["n"])
        out_vals = to_list(new_h)
        results.append({
            "id": i,
            "input": c,
            "expected": json.dumps(out_vals, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
