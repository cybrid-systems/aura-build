import bisect
import sys
import json

class TimeMap:
    def __init__(self):
        self.store = {}  # key -> {"times": [..], "values": [..]}
    
    def set(self, key: str, value: str, timestamp: int) -> None:
        if key not in self.store:
            self.store[key] = {"times": [], "values": []}
        self.store[key]["times"].append(timestamp)
        self.store[key]["values"].append(value)
    
    def get(self, key: str, timestamp: int) -> str:
        if key not in self.store:
            return ""
        times = self.store[key]["times"]
        values = self.store[key]["values"]
        # Find rightmost index where times[i] <= timestamp
        idx = bisect.bisect_right(times, timestamp) - 1
        if idx >= 0:
            return values[idx]
        return ""


def solve(operations):
    """operations: list of dicts like {"op":"SET","key":..,"value":..,"timestamp":..} or {"op":"GET","key":..,"timestamp":..}"""
    tm = TimeMap()
    results = []
    for op in operations:
        if op["op"] == "SET":
            tm.set(op["key"], op["value"], op["timestamp"])
        elif op["op"] == "GET":
            r = tm.get(op["key"], op["timestamp"])
            results.append(r)
    return results


CASES = [
    {
        "id": 0,
        "input": {
            "operations": [
                {"op": "SET", "key": "foo", "value": "bar", "timestamp": 1},
                {"op": "GET", "key": "foo", "timestamp": 1},
                {"op": "GET", "key": "foo", "timestamp": 3},
                {"op": "SET", "key": "foo", "value": "bar2", "timestamp": 4},
                {"op": "GET", "key": "foo", "timestamp": 4},
                {"op": "GET", "key": "foo", "timestamp": 5},
                {"op": "GET", "key": "foo", "timestamp": 0},
            ]
        },
        "expected": ["bar", "bar", "bar2", "bar2", ""],
    },
    {
        "id": 1,
        "input": {
            "operations": [
                {"op": "GET", "key": "missing", "timestamp": 10},
                {"op": "GET", "key": "missing", "timestamp": 0},
            ]
        },
        "expected": ["", ""],
    },
    {
        "id": 2,
        "input": {
            "operations": [
                {"op": "SET", "key": "k1", "value": "v1", "timestamp": 1},
                {"op": "SET", "key": "k1", "value": "v2", "timestamp": 2},
                {"op": "SET", "key": "k1", "value": "v3", "timestamp": 3},
                {"op": "SET", "key": "k2", "value": "a", "timestamp": 5},
                {"op": "SET", "key": "k2", "value": "b", "timestamp": 10},
                {"op": "GET", "key": "k1", "timestamp": 1},
                {"op": "GET", "key": "k1", "timestamp": 2},
                {"op": "GET", "key": "k1", "timestamp": 3},
                {"op": "GET", "key": "k2", "timestamp": 4},
                {"op": "GET", "key": "k2", "timestamp": 10},
                {"op": "GET", "key": "k2", "timestamp": 11},
            ]
        },
        "expected": ["v1", "v2", "v3", "", "b", "b"],
    },
    {
        "id": 3,
        "input": {
            "operations": [
                {"op": "GET", "key": "x", "timestamp": 1},
                {"op": "SET", "key": "x", "value": "only", "timestamp": 5},
                {"op": "GET", "key": "x", "timestamp": 4},
                {"op": "GET", "key": "x", "timestamp": 5},
                {"op": "GET", "key": "x", "timestamp": 6},
            ]
        },
        "expected": ["", "", "only", "only"],
    },
    {
        "id": 4,
        "input": {
            "operations": [
                {"op": "SET", "key": "a", "value": "x", "timestamp": 100},
                {"op": "SET", "key": "a", "value": "y", "timestamp": 200},
                {"op": "SET", "key": "a", "value": "z", "timestamp": 300},
                {"op": "SET", "key": "b", "value": "p", "timestamp": 150},
                {"op": "GET", "key": "a", "timestamp": 99},
                {"op": "GET", "key": "a", "timestamp": 100},
                {"op": "GET", "key": "a", "timestamp": 150},
                {"op": "GET", "key": "a", "timestamp": 250},
                {"op": "GET", "key": "a", "timestamp": 300},
                {"op": "GET", "key": "a", "timestamp": 301},
                {"op": "GET", "key": "b", "timestamp": 100},
                {"op": "GET", "key": "b", "timestamp": 150},
                {"op": "GET", "key": "b", "timestamp": 200},
            ]
        },
        "expected": ["", "x", "x", "y", "z", "z", "", "p", "p"],
    },
]


if __name__ == '__main__':
    out = []
    for c in CASES:
        result = solve(c["input"]["operations"])
        out.append({
            "id": c["id"],
            "input": c["input"],
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
