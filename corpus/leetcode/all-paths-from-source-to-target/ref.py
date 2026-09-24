import json
from typing import List

def solve(graph: List[List[int]]) -> List[List[int]]:
    n = len(graph)
    target = n - 1
    result: List[List[int]] = []
    path: List[int] = [0]

    def dfs(node: int) -> None:
        if node == target:
            result.append(path.copy())
            return
        for nxt in graph[node]:
            path.append(nxt)
            dfs(nxt)
            path.pop()

    dfs(0)
    return result


CASES = [
    {"graph": [[1, 2], [3], [3], []]},
    {"graph": [[1, 2], [3], [3], [4], []]},
    {"graph": [[1], [2], [3], [4], []]},
    {"graph": [[1, 2, 3], [3], [3], []]},
    {"graph": [[1], [2, 3], [3], []]},
    {"graph": [[4, 3, 1], [3, 2, 4], [3], [4], []]},
    {"graph": [[1], [2, 3], [3], [4], [5], []]},
    {"graph": [[1, 2, 3, 4, 5], [3, 4], [3, 5], [5], [5], []]},
]


def _canonical(paths: List[List[int]]) -> str:
    norm = [list(p) for p in paths]
    norm.sort()
    return json.dumps(norm, separators=(',', ':'), ensure_ascii=False)


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["graph"])
        out.append({
            "id": i,
            "input": {"graph": case["graph"]},
            "expected": _canonical(result),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
