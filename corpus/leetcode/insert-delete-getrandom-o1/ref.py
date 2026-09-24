import random
import json


class RandomizedSet:
    def __init__(self):
        self.arr = []
        self.idx = {}

    def insert(self, val: int) -> bool:
        if val in self.idx:
            return False
        self.idx[val] = len(self.arr)
        self.arr.append(val)
        return True

    def remove(self, val: int) -> bool:
        if val not in self.idx:
            return False
        i = self.idx.pop(val)
        last = self.arr[-1]
        if i != len(self.arr) - 1:
            self.arr[i] = last
            self.idx[last] = i
        self.arr.pop()
        return True

    def getRandom(self) -> int:
        return random.choice(self.arr)


def solve(operations, args):
    rs = RandomizedSet()
    results = []
    for op, arg in zip(operations, args):
        if op == "insert":
            results.append(rs.insert(arg[0]))
        elif op == "remove":
            results.append(rs.remove(arg[0]))
        elif op == "getRandom":
            results.append(rs.getRandom())
    return results


CASES = [
    {
        "operations": ["insert", "remove", "insert", "getRandom", "remove"],
        "args": [[1], [2], [2], [], [1]],
    },
    {
        "operations": ["insert", "insert", "getRandom", "remove", "getRandom"],
        "args": [[0], [1], [], [0], []],
    },
    {
        "operations": ["insert", "insert", "insert", "remove", "remove", "remove"],
        "args": [[1], [2], [3], [2], [1], [3]],
    },
    {
        "operations": ["insert", "remove", "remove"],
        "args": [[5], [5], [5]],
    },
    {
        "operations": ["insert", "insert", "insert", "getRandom"],
        "args": [[10], [20], [30], []],
    },
]


if __name__ == "__main__":
    out = []
    for i, c in enumerate(CASES):
        # Run once to capture the full trace including getRandom values.
        # For getRandom cases we set a deterministic seed so the
        # expected output is reproducible.
        random.seed(42 + i)
        result = solve(c["operations"], c["args"])
        out.append({
            "id": i,
            "input": {
                "operations": c["operations"],
                "args": c["args"],
            },
            "expected": json.dumps(result, separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
