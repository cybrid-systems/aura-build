def solve(n: int, prerequisites: list[list[int]]) -> list[int]:
    if n == 0:
        return []
    
    # Build adjacency list and in-degree count
    graph = [[] for _ in range(n)]
    in_degree = [0] * n
    
    for a, b in prerequisites:
        # a must come before b: edge a -> b
        graph[a].append(b)
        in_degree[b] += 1
    
    # Kahn's algorithm
    result = []
    queue = []
    
    for i in range(n):
        if in_degree[i] == 0:
            queue.append(i)
    
    head = 0
    while head < len(queue):
        node = queue[head]
        head += 1
        result.append(node)
        
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(result) != n:
        return []
    
    return result


CASES = [
    # Basic case with multiple valid orderings
    {"n": 4, "prerequisites": [[1, 0], [2, 0], [3, 1], [3, 2]]},
    # Simple chain
    {"n": 3, "prerequisites": [[1, 0], [2, 1]]},
    # No prerequisites - any order works
    {"n": 3, "prerequisites": []},
    # Cycle detection - should return []
    {"n": 3, "prerequisites": [[0, 1], [1, 2], [2, 0]]},
    # Self-loop cycle
    {"n": 2, "prerequisites": [[0, 0]]},
    # n = 0
    {"n": 0, "prerequisites": []},
    # Single course, no prereqs
    {"n": 1, "prerequisites": []},
    # Larger case with multiple paths
    {"n": 6, "prerequisites": [[1, 0], [2, 0], [3, 1], [4, 1], [5, 2], [5, 3]]},
    # Diamond shape
    {"n": 4, "prerequisites": [[1, 0], [2, 0], [3, 1], [3, 2]]},
    # All courses depend on one
    {"n": 5, "prerequisites": [[1, 0], [2, 0], [3, 0], [4, 0]]},
]


if __name__ == '__main__':
    import json
    
    def compute_expected(n, prereqs):
        """Compute a canonical expected ordering for the test cases.
        For some cases there are multiple valid orderings; we pick one
        canonical form here, but solve() is allowed to return any valid ordering."""
        if n == 0:
            return []
        return solve(n, prereqs)
    
    # For the expected field, we just compute solve's result. Since
    # problems accept any valid ordering, we use what solve returns.
    # But some cases have cycles, so we need to handle that.
    results = []
    for i, case in enumerate(CASES):
        n = case["n"]
        prereqs = case["prerequisites"]
        result = solve(n, prereqs)
        results.append({
            "id": i,
            "input": {"n": n, "prerequisites": prereqs},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
