def solve(head):
    dummy = ListNode(0)
    dummy.next = head
    prev = dummy
    while prev.next and prev.next.next:
        a = prev.next
        b = a.next
        prev.next = b
        a.next = b.next
        b.next = a
        prev = a
    return dummy.next


class ListNode:
    __slots__ = ('val', 'next')

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def parse_list(s):
    s = (s or '').strip()
    if not s:
        return None
    parts = s.split('->')
    nodes = [ListNode(int(p)) for p in parts]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    return nodes[0]


def to_string(node):
    vals = []
    cur = node
    seen = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        vals.append(str(cur.val))
        cur = cur.next
    return '->'.join(vals)


CASES = [
    {'s': '1->2->3->4'},
    {'s': ''},
    {'s': '1'},
    {'s': '1->2->3'},
    {'s': '1->2'},
    {'s': '1->2->3->4->5'},
    {'s': '0->0->0->0'},
    {'s': '7'},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        head = parse_list(case['s'])
        new_head = solve(head)
        out = to_string(new_head)
        results.append({'id': i, 'input': case, 'expected': json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
