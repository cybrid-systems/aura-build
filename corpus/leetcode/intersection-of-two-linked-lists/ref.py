import json

class ListNode:
    def __init__(self, val: int = 0, next: 'ListNode | None' = None):
        self.val = val
        self.next = next

def solve(headA, headB):
    # Classic two-pointer technique: when a pointer reaches end of its list,
    # redirect it to the head of the other list. After at most n+m steps,
    # they either meet at the intersection or both become None.
    if headA is None or headB is None:
        return None
    pA, pB = headA, headB
    # We iterate at most (n+m+1) times; using a counter is safer than a
    # "while pA != pB" loop in case of weird inputs (though classic form is fine).
    max_steps = 0
    while pA != pB:
        pA = pA.next if pA else headB
        pB = pB.next if pB else headA
        max_steps += 1
        if max_steps > 1000000:  # safety guard against truly broken inputs
            return None
    return pA


# ---- Test harness ----

def build_list(spec):
    """
    spec: dict like {'nodes': [v1, v2, ...], 'tail': idx or None}
    where 'tail' is the index of a node that ends the list (its .next stays None).
    Or a simple list of values (tail = last index).
    """
    if isinstance(spec, list):
        values = spec
        tail_idx = len(values) - 1
    else:
        values = spec['nodes']
        tail_idx = spec.get('tail', len(values) - 1)
    nodes = [ListNode(v) for v in values]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    # Mark the tail
    nodes[tail_idx].next = None
    return nodes, tail_idx


def build_intersecting(A_vals, B_vals_before, shared_vals, intersect_at_A_idx):
    """
    Build A and B where B's tail joins A at node A[intersect_at_A_idx].
    A = A_vals + shared_vals
    B = B_vals_before + shared_vals
    The intersection is A[intersect_at_A_idx].
    """
    A_full = A_vals + shared_vals
    B_full = B_vals_before + shared_vals
    A_nodes = [ListNode(v) for v in A_full]
    B_nodes = [ListNode(v) for v in B_full]
    # Link A
    for i in range(len(A_nodes) - 1):
        A_nodes[i].next = A_nodes[i + 1]
    A_nodes[-1].next = None
    # Link B up to the shared part; B's pre-shared tail's next points to A's intersection node
    shared_start_in_B = len(B_vals_before)
    for i in range(shared_start_in_B - 1):
        B_nodes[i].next = B_nodes[i + 1]
    if shared_start_in_B > 0:
        B_nodes[shared_start_in_B - 1].next = A_nodes[intersect_at_A_idx]
    else:
        # B starts directly at the shared node (intersect_at_A_idx == 0)
        pass
    # B's head:
    B_head = A_nodes[intersect_at_A_idx] if shared_start_in_B == 0 else B_nodes[0]
    return A_nodes[0], B_head, A_nodes[intersect_at_A_idx]


CASES = [
    # Case 0: classic LeetCode example
    # A = 4->1->8->4->5, B = 5->6->1->8->4->5, intersection at val=8 (A index 2)
    {
        'kind': 'intersect',
        'A_vals': [4, 1, 8, 4, 5],
        'B_before': [5, 6, 1],
        'shared': [8, 4, 5],
        'intersect_at_A': 2,
    },
    # Case 1: disjoint lists
    {
        'kind': 'disjoint',
        'A_vals': [2, 6, 4],
        'B_vals': [1, 5],
    },
    # Case 2: same node (both heads point to same node)
    # A = 1->2, B = 1->2 (but actually A=[1], B=[1,2] sharing at index 0)
    # Let's do: A=[1,2,3], B=[] (B is empty before shared), shared=[3,4], intersect at A index 2
    {
        'kind': 'intersect',
        'A_vals': [1, 2, 3],
        'B_before': [],
        'shared': [3, 4],
        'intersect_at_A': 2,
    },
    # Case 3: B entirely within A (B shares a middle node of A)
    # A = 1->2->3->4, B = 9->3->4, intersection at A[2]=3
    {
        'kind': 'intersect',
        'A_vals': [1, 2, 3, 4],
        'B_before': [9],
        'shared': [3, 4],
        'intersect_at_A': 2,
    },
    # Case 4: intersection at the very first node of A
    # A = 7->8->9, B = 1->7->8->9 (intersect at A[0])
    {
        'kind': 'intersect',
        'A_vals': [7, 8, 9],
        'B_before': [1],
        'shared': [7, 8, 9],
        'intersect_at_A': 0,
    },
    # Case 5: both single nodes, same node -> intersection
    {
        'kind': 'intersect',
        'A_vals': [42],
        'B_before': [],
        'shared': [42],
        'intersect_at_A': 0,
    },
    # Case 6: one list is None -> return None
    {
        'kind': 'disjoint',
        'A_vals': [],
        'B_vals': [1, 2, 3],
    },
    # Case 7: longish intersecting lists
    {
        'kind': 'intersect',
        'A_vals': [1, 2, 3, 4, 5, 6, 7],
        'B_before': [10, 11],
        'shared': [99, 100, 101],
        'intersect_at_A': 7,
    },
]


def make_case(case):
    if case['kind'] == 'intersect':
        A, B, expected_node = build_intersecting(
            case['A_vals'], case['B_before'], case['shared'], case['intersect_at_A']
        )
        # For 'disjoint' we have no expected node; for 'intersect' we use identity
        return {'A': A, 'B': B, 'expected': expected_node}
    else:
        # disjoint
        A_vals = case['A_vals']
        B_vals = case['B_vals']
        A_nodes = [ListNode(v) for v in A_vals]
        B_nodes = [ListNode(v) for v in B_vals]
        for i in range(len(A_nodes) - 1):
            A_nodes[i].next = A_nodes[i + 1]
        if A_nodes:
            A_nodes[-1].next = None
        for i in range(len(B_nodes) - 1):
            B_nodes[i].next = B_nodes[i + 1]
        if B_nodes:
            B_nodes[-1].next = None
        return {'A': (A_nodes[0] if A_nodes else None),
                'B': (B_nodes[0] if B_nodes else None),
                'expected': None}


def node_id(node):
    """Return a canonical identifier for a node for JSON serialization."""
    if node is None:
        return None
    # Use id() but normalize: we'll store as 'N@id' so it's distinguishable
    # but the harness compares by `is` identity anyway.
    return f"node@{id(node)}"


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        built = make_case(case)
        headA = built['A']
        headB = built['B']
        expected = built['expected']
        result = solve(headA, headB)
        results.append({
            'id': i,
            'input': {
                'headA_id': node_id(headA),
                'headB_id': node_id(headB),
            },
            'expected': node_id(expected),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
