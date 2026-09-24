from collections import deque
import json

def solve(operations: list[list]) -> list:
    q1 = deque()
    q2 = deque()
    results = []
    
    for op in operations:
        if not op:
            continue
        cmd = op[0]
        if cmd == "push":
            x = op[1]
            q2.append(x)
            while q1:
                q2.append(q1.popleft())
            q1, q2 = q2, q1
        elif cmd == "pop":
            results.append(q1.popleft())
        elif cmd == "top":
            results.append(q1[0])
        elif cmd == "empty":
            results.append(len(q1) == 0)
    
    return results


CASES = [
    {"operations": [["push", 1], ["push", 2], ["top"], ["pop"]]},
    {"operations": []},
    {"operations": [["push", 1], ["pop"], ["empty"]]},
    {"operations": [["push", 1], ["push", 2], ["push", 3], ["pop"], ["pop"], ["pop"], ["empty"]]},
    {"operations": [["empty"]]},
    {"operations": [["push", 42], ["top"], ["top"], ["pop"], ["empty"], ["push", 7], ["top"], ["pop"]]},
    {"operations": [["push", 5], ["push", 10], ["pop"], ["push", 15], ["top"], ["pop"], ["pop"], ["empty"]]},
]


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        canonical = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        out.append({"id": i, "input": case, "expected": canonical})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
