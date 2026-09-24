def solve(successors: list[int]) -> int:
    n = len(successors)
    head = -1
    for i, v in enumerate(successors):
        if v == -1:
            head = i
            break
    if head == -1:
        return -1
    slow = head
    fast = head
    while True:
        s_next = successors[slow]
        if s_next < 0:
            return -1
        slow = s_next
        f_next1 = successors[fast]
        if f_next1 < 0:
            return -1
        f_next2 = successors[f_next1]
        if f_next2 < 0:
            return -1
        fast = f_next2
        if slow == fast:
            break
    slow = head
    while slow != fast:
        slow = successors[slow]
        fast = successors[fast]
    return slow


CASES = [
    {"successors": [1, 2, 3, 0, -2]},
    {"successors": [-2, 0]},
    {"successors": [1, 0]},
    {"successors": [-2]},
    {"successors": [0]},
    {"successors": [1, 2, 0, -2]},
    {"successors": [2, 0, 1, -2]},
    {"successors": [-2, 1, 2, 3, 4]},
    {"successors": [1, 2, 3, 4, 5, 0, -2]},
    {"successors": [1, 0, 2, 3, -2]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
