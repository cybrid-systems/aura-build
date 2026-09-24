import json
from collections import deque

class Codec:
    def serialize(self, root):
        """Encodes a tree to a single string.
        Format: comma-separated level-order with '#' as null.
        """
        if root is None:
            return ""
        parts = []
        queue = deque([root])
        # We need to know when all remaining nodes are nulls to stop,
        # but for round-trip we can encode using level-order and keep nulls.
        # To stay invertible we encode full level-order including nulls,
        # until we've added all nodes of last level (trailing nulls omitted).
        while queue:
            node = queue.popleft()
            if node is None:
                parts.append("#")
                continue
            parts.append(str(node.val))
            queue.append(node.left)
            queue.append(node.right)
        # Strip trailing '#' so round-trip stays clean but still unambiguous.
        while parts and parts[-1] == "#":
            parts.pop()
        return ",".join(parts)

    def deserialize(self, data):
        """Decodes your encoded data to tree.
        We store nulls in a list and reconstruct via a queue indexing scheme.
        """
        if not data:
            return None
        tokens = data.split(",")
        # Pad with nulls up to len(tokens) so every token maps to a node slot.
        nodes = [None] * len(tokens)
        for i, t in enumerate(tokens):
            if t == "#":
                nodes[i] = None
            else:
                n = Node(int(t))
                nodes[i] = n
        root = nodes[0]
        if root is None:
            return None
        # Reconnect children: for node at index i (1-based, parent at (i+1)//2 - 1).
        # Use 0-based indexing: parent i has left child at 2*i+1, right at 2*i+2.
        # Only valid when slot exists in nodes list.
        for i in range(len(tokens)):
            n = nodes[i]
            if n is None:
                continue
            li = 2 * i + 1
            ri = 2 * i + 2
            if li < len(nodes):
                n.left = nodes[li]
            if ri < len(nodes):
                n.right = nodes[ri]
        return root


class Node:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def tree_to_levels(root):
    """Return level-order list with '#' for missing children at each level boundary."""
    if root is None:
        return []
    result = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            result.append("#")
            continue
        result.append(node.val)
        q.append(node.left)
        q.append(node.right)
    # No trimming here because callers compare to original input which may
    # explicitly contain trailing nulls in some cases. For equality we don't
    # trim so it matches the canonical input lists (e.g., [1,2,3,'#','#',4,5]).
    return result


def build_from_levels(values):
    """Build a tree from a level-order list. '#' or None means null."""
    if not values:
        return None
    it = iter(values)
    first = next(it)
    if first is None or first == "#":
        return None
    root = Node(first)
    q = deque([root])
    while q:
        node = q.popleft()
        # Try left
        try:
            lv = next(it)
        except StopIteration:
            lv = None
        if lv is not None and lv != "#":
            node.left = Node(lv)
            q.append(node.left)
        else:
            node.left = None
        # Try right
        try:
            rv = next(it)
        except StopIteration:
            rv = None
        if rv is not None and rv != "#":
            node.right = Node(rv)
            q.append(node.right)
        else:
            node.right = None
    return root


def solve(root_levels):
    """Serialize then deserialize and compare to original."""
    root = build_from_levels(root_levels)
    c = Codec()
    s = c.serialize(root)
    r = c.deserialize(s)
    out_levels = tree_to_levels(r)
    # Canonicalize: integers as ints, '#' for nulls in our out.
    return s, out_levels


CASES = [
    {"root": [1, 2, 3, "#", "#", 4, 5]},
    {"root": []},
    {"root": [7]},
    {"root": [1, 2, 3, 4, 5, "#", "#"]},
    {"root": [0, "#", 1]},
    {"root": [1, "#", 2, "#", 3]},
    {"root": [5, 4, 7, 3, "#", 6, 8]},
    {"root": [10, 5, 15, "#", 6, 12, 20]},
]

if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        s, levels = solve(case["root"])
        results.append({
            "id": i,
            "input": {"root": case["root"]},
            "expected": json.dumps([s, levels], separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))
