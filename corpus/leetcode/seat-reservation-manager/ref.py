import json

class SeatManager:
    def __init__(self, n: int):
        self.n = n
        self.next_seat = 1
        self.heap = []

    def reserve(self) -> int:
        if self.heap:
            return self.heap.pop(0) if False else None  # placeholder
        # proper implementation below
        return -1

    def unreserve(self, seatNumber: int) -> None:
        pass

import heapq

class SeatManager2:
    def __init__(self, n: int):
        self.next_seat = 1
        self.n = n
        self.heap = []

    def reserve(self) -> int:
        if self.heap:
            return heapq.heappop(self.heap)
        seat = self.next_seat
        self.next_seat += 1
        return seat

    def unreserve(self, seatNumber: int) -> None:
        heapq.heappush(self.heap, seatNumber)


def solve(n: int, operations: list[tuple[str, int | None]]) -> list[int | None]:
    manager = SeatManager2(n)
    results = []
    for op, val in operations:
        if op == "reserve":
            results.append(manager.reserve())
        elif op == "unreserve":
            manager.unreserve(val)
    return results


CASES = [
    {
        "n": 5,
        "operations": [("reserve", None), ("reserve", None), ("unreserve", 2), ("reserve", None)],
    },
    {
        "n": 1,
        "operations": [("reserve", None), ("reserve", None), ("unreserve", 1), ("reserve", None)],
    },
    {
        "n": 10,
        "operations": [("reserve", None)] * 5 + [("unreserve", 3), ("reserve", None), ("unreserve", 1), ("reserve", None)],
    },
    {
        "n": 3,
        "operations": [("unreserve", 1), ("reserve", None)],
    },
    {
        "n": 4,
        "operations": [("reserve", None), ("unreserve", 1), ("reserve", None), ("unreserve", 2), ("reserve", None), ("reserve", None)],
    },
]


if __name__ == '__main__':
    output = []
    for i, case in enumerate(CASES):
        kwargs = dict(case)
        result = solve(**kwargs)
        # canonical encoding per problem statement
        encoded_input = json.dumps({"n": case["n"], "operations": case["operations"]}, separators=(',', ':'), ensure_ascii=False)
        output.append({"id": i, "input": json.loads(encoded_input), "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
