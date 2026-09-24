from collections import deque
import json

class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []

def solve(start):
    if start is None:
        return None
    if not start.neighbors:
        return Node(start.val, [])
    # Build clone map
    clones = {id(start): Node(start.val, [])}
    # BFS using stacks of edges (original, parent_clone)
    stack = [(start, clones[id(start)])]
    visited = {id(start)}
    while stack:
        orig, parent_clone = stack.pop()
        for nb in orig.neighbors:
            if id(nb) not in clones:
                clones[id(nb)] = Node(nb.val, [])
            if id(nb) not in visited:
                visited.add(id(nb))
                stack.append((nb, clones[id(nb)]))
            parent_clone.neighbors.append(clones[id(nb)])
    return clones[id(start)]

def _adj_list(node):
    """Return adjacency list: {node_id: [neighbor_ids]} via BFS, for canonicalization."""
    if node is None:
        return {}
    seen = {}
    # Map old id() to its val
    queue = deque([node])
    seen[id(node)] = node
    result = {}
    while queue:
        cur = queue.popleft()
        result[cur.val] = sorted(nb.val for nb in cur.neighbors)
        for nb in cur.neighbors:
            if id(nb) not in seen:
                seen[id(nb)] = nb
                queue.append(nb)
    return result

def _build_graph(spec):
    """Build a graph from adjacency list spec {node_id: [neighbor_ids]}.
    Returns the node with the smallest id as the start node.
    """
    nodes = {k: Node(k) for k in spec}
    for k, neighs in spec.items():
        nodes[k].neighbors = [nodes[n] for n in neighs]
    # Return node with smallest id as start
    return nodes[min(spec.keys())] if spec else None

CASES = [
    # single node, no neighbors
    {"spec": {1: []}},
    # two connected nodes
    {"spec": {1: [2], 2: [1]}},
    # 3 nodes triangle
    {"spec": {1: [2,3], 2: [1,3], 3: [1,2]}},
    # 4 nodes in a line
    {"spec": {1: [2], 2: [1,3], 3: [2,4], 4: [3]}},
    # 5 nodes star
    {"spec": {1: [2,3,4,5], 2: [1], 3: [1], 4: [1], 5: [1]}},
    # 4 nodes with one extra edge
    {"spec": {1: [2,3], 2: [1,3], 3: [1,2,4], 4: [3]}},
    # start at node 2 not node 1
    {"spec": {1: [2], 2: [1]}, "start_id": 2},
    # single edge, start at leaf
    {"spec": {1: [2], 2: [1]}, "start_id": 2},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        spec = case["spec"]
        start_node = _build_graph(spec)
        if "start_id" in case:
            # Rebuild to pick start
            nodes = {k: Node(k) for k in spec}
            for k, neighs in spec.items():
                nodes[k].neighbors = [nodes[n] for n in neighs]
            start_node = nodes[case["start_id"]]
        cloned = solve(start_node)
        # Canonical form: adjacency list by node val
        canonical = json.dumps(_adj_list(cloned), sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        # Also verify it's a deep copy (no shared ids)
        deep_ok = cloned is not start_node
        # Verify neighbors are different objects
        if cloned is not None and cloned.neighbors:
            deep_ok = deep_ok and all(cn is not on for cn, on in zip(cloned.neighbors, start_node.neighbors))
        results.append({
            "id": i,
            "input": case,
            "expected": canonical,
            "deep_copy_ok": deep_ok,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
