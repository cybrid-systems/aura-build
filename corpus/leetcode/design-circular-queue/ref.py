import sys
import json

class CircularQueue:
    def __init__(self, capacity):
        self.cap = capacity
        self.arr = [0] * capacity
        self.head = 0
        self.tail = 0
        self.count = 0
    
    def enqueue(self, value):
        if self.count == self.cap:
            return False
        self.arr[self.tail] = value
        self.tail = (self.tail + 1) % self.cap
        self.count += 1
        return True
    
    def dequeue(self):
        if self.count == 0:
            return False
        self.head = (self.head + 1) % self.cap
        self.count -= 1
        return True
    
    def front(self):
        if self.count == 0:
            return -1
        return self.arr[self.head]
    
    def rear(self):
        if self.count == 0:
            return -1
        # tail points one past the last element
        idx = (self.tail - 1) % self.cap
        return self.arr[idx]
    
    def is_empty(self):
        return self.count == 0
    
    def is_full(self):
        return self.count == self.cap


def solve(commands, capacity):
    q = CircularQueue(capacity)
    out = []
    for cmd in commands:
        op = cmd[0]
        if op == "enqueue":
            out.append(q.enqueue(cmd[1]))
        elif op == "dequeue":
            out.append(q.dequeue())
        elif op == "front":
            out.append(q.front())
        elif op == "rear":
            out.append(q.rear())
        elif op == "is_empty":
            out.append(q.is_empty())
        elif op == "is_full":
            out.append(q.is_full())
    return out


CASES = [
    # The example from the problem (computed logically)
    {
        "capacity": 5,
        "commands": [
            ["enqueue", 1], ["enqueue", 2], ["enqueue", 3], ["enqueue", 4], ["enqueue", 5],
            ["is_full"], ["dequeue"], ["enqueue", 6], ["front"], ["rear"],
            ["dequeue"], ["dequeue"], ["dequeue"], ["dequeue"], ["dequeue"],
            ["is_empty"], ["front"], ["rear"]
        ]
    },
    # Simple wrap-around
    {
        "capacity": 3,
        "commands": [
            ["enqueue", 10], ["enqueue", 20], ["enqueue", 30],
            ["is_full"], ["rear"], ["front"],
            ["dequeue"], ["enqueue", 40], ["front"], ["rear"], ["is_full"]
        ]
    },
    # Capacity 1 edge case
    {
        "capacity": 1,
        "commands": [
            ["is_empty"], ["is_full"], ["front"], ["rear"],
            ["enqueue", 7], ["is_full"], ["front"], ["rear"],
            ["enqueue", 8], ["dequeue"], ["front"], ["is_empty"]
        ]
    },
    # Operations on empty queue
    {
        "capacity": 2,
        "commands": [
            ["front"], ["rear"], ["dequeue"], ["is_empty"], ["is_full"]
        ]
    },
    # Multiple wrap-arounds
    {
        "capacity": 4,
        "commands": [
            ["enqueue", 1], ["enqueue", 2], ["dequeue"], ["dequeue"],
            ["enqueue", 3], ["enqueue", 4], ["enqueue", 5], ["enqueue", 6],
            ["front"], ["rear"], ["is_full"]
        ]
    },
    # No operations case (just queries)
    {
        "capacity": 3,
        "commands": [["is_empty"], ["is_full"], ["front"], ["rear"]]
    },
]


if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["commands"], case["capacity"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
