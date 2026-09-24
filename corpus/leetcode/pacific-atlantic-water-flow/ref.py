def solve(heights):
    if not heights or not heights[0]:
        return []
    m, n = len(heights), len(heights[0])
    
    def bfs(starts):
        visited = [[False]*n for _ in range(m)]
        from collections import deque
        q = deque()
        for r, c in starts:
            visited[r][c] = True
            q.append((r, c))
        while q:
            r, c = q.popleft()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < m and 0 <= nc < n and not visited[nr][nc]:
                    if heights[nr][nc] >= heights[r][c]:
                        visited[nr][nc] = True
                        q.append((nr, nc))
        return visited
    
    pacific_starts = [(0, c) for c in range(n)] + [(r, 0) for r in range(1, m)]
    atlantic_starts = [(m-1, c) for c in range(n)] + [(r, n-1) for r in range(m-1)]
    
    pac = bfs(pacific_starts)
    atl = bfs(atlantic_starts)
    
    result = []
    for r in range(m):
        for c in range(n):
            if pac[r][c] and atl[r][c]:
                result.append([r, c])
    return result


CASES = [
    {"heights": [[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],[6,7,1,4,5],[5,1,1,2,4]]},
    {"heights": [[1]]},
    {"heights": [[1,2],[2,3]]},
    {"heights": [[2,1],[1,2]]},
    {"heights": [[1,2,3],[4,5,6],[7,8,9]]},
    {"heights": [[10,10,10],[10,10,10],[10,10,10]]},
    {"heights": [[1,2],[3,4]]},
    {"heights": [[5,4,3],[4,3,2],[3,2,1]]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        # Canonicalize: sort the list of coords for deterministic output
        canonical = sorted([list(p) for p in result])
        out.append({"id": i, "input": case, "expected": json.dumps(canonical, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
