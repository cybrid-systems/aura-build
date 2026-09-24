from __future__ import annotations
import json
from typing import List, Optional, Iterable


class _Node:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key: int, val: int) -> None:
        self.key = key
        self.val = val
        self.prev: Optional[_Node] = None
        self.next: Optional[_Node] = None


class LRUCache:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.cap = capacity
        self.map: dict[int, _Node] = {}
        # Sentinel head/tail for O(1) ops without boundary checks
        self.head = _Node(0, 0)
        self.tail = _Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, node: _Node) -> None:
        p, n = node.prev, node.next
        if p is not None:
            p.next = n
        if n is not None:
            n.prev = p
        node.prev = None
        node.next = None

    def _add_to_front(self, node: _Node) -> None:
        node.next = self.head.next
        node.prev = self.head
        if self.head.next is not None:
            self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        node = self.map.get(key)
        if node is None:
            return -1
        self._remove(node)
        self._add_to_front(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        node = self.map.get(key)
        if node is not None:
            node.val = value
            self._remove(node)
            self._add_to_front(node)
            return
        if len(self.map) >= self.cap:
            lru = self.tail.prev
            assert lru is not None and lru is not self.head
            self._remove(lru)
            self.map.pop(lru.key, None)
        new_node = _Node(key, value)
        self._add_to_front(new_node)
        self.map[key] = new_node


# --- Reference solve driver used by the harness ---
def solve(ops: List[object]) -> List[int]:
    """
    ops is a list of commands in the textual/log form:
      ["init", C]
      ["put", K, V]
      ["get", K]   -> produces a return value
    Returns the list of return values from every 'get' call, in order.
    """
    if not ops:
        return []
    if ops[0][0] != "init":
        raise ValueError("first op must be init")
    cache = LRUCache(int(ops[0][1]))
    out: List[int] = []
    for op in ops[1:]:
        kind = op[0]
        if kind == "put":
            cache.put(int(op[1]), int(op[2]))
        elif kind == "get":
            out.append(cache.get(int(op[1])))
        else:
            raise ValueError(f"unknown op {kind!r}")
    return out


# Canonical JSON encoder used for the harness output.
def _canon(x):
    if isinstance(x, bool):
        return "true" if x else "false"
    raise TypeError(type(x))


CASES = [
    # Classic example from LeetCode
    {
        "ops": [
            ["init", 2],
            ["put", 1, 1],
            ["put", 2, 2],
            ["get", 1],
            ["put", 3, 3],
            ["get", 2],
            ["put", 4, 4],
            ["get", 1],
            ["get", 3],
            ["get", 4],
        ]
    },
    # Updates do not evict and refresh recency
    {
        "ops": [
            ["init", 2],
            ["put", 1, 1],
            ["put", 2, 2],
            ["get", 1],   # marks 1 as MRU
            ["put", 1, 10],  # update, no eviction
            ["get", 1],
            ["put", 3, 3],   # evicts key 2
            ["get", 2],
            ["get", 3],
        ]
    },
    # Single capacity
    {
        "ops": [
            ["init", 1],
            ["put", 5, 5],
            ["get", 5],
            ["put", 6, 6],  # evicts 5
            ["get", 5],
            ["get", 6],
        ]
    },
    # Repeated access without writes
    {
        "ops": [
            ["init", 3],
            ["put", 1, 100],
            ["put", 2, 200],
            ["put", 3, 300],
            ["get", 1], ["get", 2], ["get", 3], ["get", 1], ["get", 2],
            ["get", 1], ["get", 3], ["get", 2],
        ]
    },
    # Many misses
    {
        "ops": [
            ["init", 2],
            ["get", 0],
            ["get", 1],
            ["put", 2, 1],
            ["get", 0],
            ["get", 2],
            ["put", 3, 2],
            ["get", 0],
            ["get", 2],
            ["get", 3],
        ]
    },
    # Larger workload with churn
    {
        "ops": [
            ["init", 3],
            ["put", 1, 1], ["put", 2, 2], ["put", 3, 3],
            ["put", 4, 4],   # evicts 1
            ["put", 2, 22],  # update 2
            ["put", 5, 5],   # evicts 3 (LRU), since 4 was accessed by insertion only? LRU order after ops: 2(MRU),4,3 -> evicts 3
            ["get", 1], ["get", 2], ["get", 3], ["get", 4], ["get", 5],
            ["get", 6],
        ]
    },
    # Capacity 1 with repeated same key
    {
        "ops": [
            ["init", 1],
            ["put", 1, 1], ["put", 1, 2], ["put", 1, 3],
            ["get", 1],
            ["put", 2, 9],
            ["get", 1],
            ["get", 2],
        ]
    },
]


if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["ops"])
        results.append({
            "id": i,
            "input": {"ops": case["ops"]},
            "expected": json.dumps(out, separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))
