def solve(parent, left, right):
    n = len(parent)
    if n == 0:
        return 0
    
    # Build children adjacency
    children = [[] for _ in range(n)]
    root = -1
    for i in range(n):
        if parent[i] == -1:
            root = i
        else:
            children[parent[i]].append(i)
    
    # States: 0 = needs monitoring, 1 = has camera, 2 = already covered
    cameras = 0
    
    def dfs(node):
        nonlocal cameras
        # Returns state of this node
        # First, get states of children
        child_states = []
        for c in children[node]:
            child_states.append(dfs(c))
        
        # If all children are covered (state 2) and there are children,
        # then this node is covered by children
        # But we need to determine based on children states:
        # - If any child needs monitoring (state 0): place camera here
        # - If any child has camera (state 1): this node is covered
        # - If all children are covered (state 2): this node needs monitoring
        
        has_camera_child = False
        needs_monitoring_child = False
        
        for s in child_states:
            if s == 0:
                needs_monitoring_child = True
            elif s == 1:
                has_camera_child = True
        
        if needs_monitoring_child:
            cameras += 1
            return 1  # has camera
        elif has_camera_child:
            return 2  # covered by child
        else:
            return 0  # needs monitoring
    
    result = dfs(root)
    
    # If root still needs monitoring, place camera there
    if result == 0:
        cameras += 1
    
    return cameras


CASES = [
    {"parent": [4, -1, 4, 0, 1], "left": [1, 3, -1, -1, -1], "right": [2, -1, -1, -1, -1]},
    {"parent": [-1, 0, 0], "left": [1, 2, -1], "right": [-1, -1, -1]},
    {"parent": [-1], "left": [-1], "right": [-1]},
    {"parent": [-1, 0], "left": [1, -1], "right": [-1, -1]},
    {"parent": [-1, 0, 0, 1, 1], "left": [1, 2, -1, -1, -1], "right": [3, 4, -1, -1, -1]},
    {"parent": [-1, 0, 0], "left": [1, -1], "right": [2, -1]},
    {"parent": [-1, 0, 1], "left": [1, 2, -1], "right": [-1, -1, -1]},
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        result = solve(case["parent"], case["left"], case["right"])
        results.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
