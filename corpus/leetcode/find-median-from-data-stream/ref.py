import sys
import json
import heapq


class MedianFinder:
    def __init__(self):
        self.lo = []  # max-heap (negated) for lower half
        self.hi = []  # min-heap for upper half

    def add(self, num):
        # Push to appropriate heap first
        if not self.lo or num <= -self.lo[0]:
            heapq.heappush(self.lo, -num)
        else:
            heapq.heappush(self.hi, num)
        # Rebalance: |len(lo) - len(hi)| <= 1, and len(lo) >= len(hi)
        if len(self.lo) > len(self.hi) + 1:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))
        elif len(self.hi) > len(self.lo):
            heapq.heappush(self.lo, -heapq.heappop(self.hi))

    def median(self):
        if len(self.lo) > len(self.hi):
            return float(-self.lo[0])
        return (-self.lo[0] + self.hi[0]) / 2.0


def solve(commands):
    """Process a list of commands.

    Each command is either ("ADD", int) or ("MEDIAN",).
    Returns a list of float median values, one per MEDIAN command.
    """
    mf = MedianFinder()
    results = []
    for cmd in commands:
        op = cmd[0]
        if op == "ADD":
            mf.add(int(cmd[1]))
        elif op == "MEDIAN":
            results.append(mf.median())
    return results


CASES = [
    # Example from the problem statement
    {"commands": [
        ("ADD", 1), ("MEDIAN",),
        ("ADD", 2), ("MEDIAN",),
        ("ADD", 3), ("MEDIAN",),
    ]},
    # Single element
    {"commands": [("ADD", 42), ("MEDIAN",)]},
    # Two elements (even count, average)
    {"commands": [("ADD", 10), ("ADD", 20), ("MEDIAN",)]},
    # Negative numbers
    {"commands": [
        ("ADD", -5), ("MEDIAN",),
        ("ADD", -1), ("MEDIAN",),
        ("ADD", -3), ("MEDIAN",),
        ("ADD", -7), ("MEDIAN",),
    ]},
    # Interleaved add/median, duplicates, zero
    {"commands": [
        ("ADD", 0), ("MEDIAN",),
        ("ADD", 0), ("MEDIAN",),
        ("ADD", 0), ("MEDIAN",),
        ("ADD", 5), ("MEDIAN",),
        ("ADD", -5), ("MEDIAN",),
    ]},
    # Unsorted insertion order
    {"commands": [
        ("ADD", 7), ("ADD", 1), ("ADD", 9), ("ADD", 4),
        ("ADD", 6), ("ADD", 2), ("ADD", 8), ("MEDIAN",),
        ("ADD", 5), ("MEDIAN",),
        ("ADD", 3), ("MEDIAN",),
    ]},
    # Larger values, many medians
    {"commands": [("ADD", i) for i in [100, 50, 200, 25, 75, 150, 250]]
              + [("MEDIAN",)] * 7},
    # Edge: alternating tiny and large, many medians
    {"commands": (
        [("ADD", 1), ("MEDIAN",),
         ("ADD", 1000000), ("MEDIAN",),
         ("ADD", 2), ("MEDIAN",),
         ("ADD", 999999), ("MEDIAN",),
         ("ADD", 500000), ("MEDIAN",)]
    )},
]


if __name__ == "__main__":
    out = []
    for i, case in enumerate(CASES):
        commands = case["commands"]
        result = solve(commands)
        # Canonical string of the result list
        expected = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        out.append({
            "id": i,
            "input": {"commands": commands},
            "expected": expected,
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
