class ListNode:
    def __init__(self, val: int = 0, next=None):
        self.val = val
        self.next = next

def build_list(tokens):
    if not tokens:
        return None, -1
    # tokens: list of integers, last may be the cycle index
    # We need to detect where END is in the input line; the harness gives tokens after CASE0=
    # Per problem: tokens before END are values; token after END (if any) is k, or missing/-1 means no cycle.
    # Find END marker.
    if 'END' in tokens:
        idx = tokens.index('END')
        vals = [int(x) for x in tokens[:idx]]
        k_tokens = tokens[idx+1:]
        k = int(k_tokens[0]) if k_tokens and k_tokens[0] != '-1' else (-1 if not k_tokens else -1)
    else:
        vals = [int(x) for x in tokens]
        k = -1

    if not vals:
        return None, k

    nodes = [ListNode(v) for v in vals]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i+1]

    head = nodes[0]
    if k >= 0 and k < len(nodes):
        nodes[-1].next = nodes[k]
    else:
        nodes[-1].next = None

    return head, k

def has_cycle(head):
    if head is None:
        return False
    slow = head
    fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False

def solve(head):
    return has_cycle(head)

CASES = [
    {"tokens": ["3", "2", "0", "-4", "END", "1"]},
    {"tokens": ["1", "2", "END"]},
    {"tokens": ["1", "END"]},
    {"tokens": ["END"]},
    {"tokens": ["1", "2", "3", "4", "5", "END", "0"]},
    {"tokens": ["1", "2", "3", "END", "2"]},
    {"tokens": ["1", "2", "3", "4", "END", "-1"]},
    {"tokens": ["0", "END"]},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        head, k = build_list(case["tokens"])
        result = solve(head)
        results.append({
            "id": i,
            "input": {"tokens": case["tokens"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
