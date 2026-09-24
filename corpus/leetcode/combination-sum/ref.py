from typing import List

def solve(candidates: List[int], target: int) -> List[List[int]]:
    candidates = sorted(candidates)
    result: List[List[int]] = []
    combo: List[int] = []

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(combo.copy())
            return
        for i in range(start, len(candidates)):
            c = candidates[i]
            if c > remaining:
                break
            combo.append(c)
            backtrack(i, remaining - c)
            combo.pop()

    backtrack(0, target)
    return result


CASES = [
    {"candidates": [2, 3, 6, 7], "target": 7},
    {"candidates": [2, 3, 5], "target": 8},
    {"candidates": [2], "target": 1},
    {"candidates": [1], "target": 1},
    {"candidates": [1], "target": 5},
    {"candidates": [3, 5, 8, 10], "target": 11},
    {"candidates": [2, 4, 6, 8], "target": 16},
    {"candidates": [7, 3, 2, 6], "target": 7},
]


def canonical(combs: List[List[int]]) -> List[List[int]]:
    return sorted([sorted(c) for c in combs])


if __name__ == "__main__":
    import json

    out = []
    for idx, case in enumerate(CASES):
        cands = case["candidates"]
        tgt = case["target"]
        got = canonical(solve(cands, tgt))
        out.append({
            "id": idx,
            "input": {"candidates": cands, "target": tgt},
            "expected": json.dumps(got, separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
