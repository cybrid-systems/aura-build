import json

class _Node:
    __slots__ = ('val', 'next')
    def __init__(self, val=0, nxt=None):
        self.val = val
        self.next = nxt

class MyLinkedList:
    def __init__(self):
        self.head = None
        self.size = 0

    def get(self, index: int) -> int:
        if index < 0 or index >= self.size:
            return -1
        cur = self.head
        for _ in range(index):
            cur = cur.next
        return cur.val

    def addAtHead(self, val: int) -> None:
        self.head = _Node(val, self.head)
        self.size += 1

    def addAtTail(self, val: int) -> None:
        new_node = _Node(val)
        if self.head is None:
            self.head = new_node
        else:
            cur = self.head
            while cur.next is not None:
                cur = cur.next
            cur.next = new_node
        self.size += 1

    def addAtIndex(self, index: int, val: int) -> None:
        if index > self.size:
            return
        if index <= 0:
            self.addAtHead(val)
            return
        cur = self.head
        for _ in range(index - 1):
            cur = cur.next
        cur.next = _Node(val, cur.next)
        self.size += 1

    def deleteAtIndex(self, index: int) -> None:
        if index < 0 or index >= self.size:
            return
        if index == 0:
            self.head = self.head.next
        else:
            cur = self.head
            for _ in range(index - 1):
                cur = cur.next
            cur.next = cur.next.next
        self.size -= 1


def solve(n, ops):
    ll = MyLinkedList()
    results = []
    for op in ops:
        name = op[0]
        if name == "MyLinkedList":
            continue
        if name == "get":
            results.append(ll.get(op[1]))
        elif name == "addAtHead":
            ll.addAtHead(op[1])
        elif name == "addAtTail":
            ll.addAtTail(op[1])
        elif name == "addAtIndex":
            ll.addAtIndex(op[1], op[2])
        elif name == "deleteAtIndex":
            ll.deleteAtIndex(op[1])
    return results


CASES = [
    {
        "n": 7,
        "ops": [["MyLinkedList"], ["addAtHead", 1], ["addAtTail", 3],
                ["addAtIndex", 1, 2], ["get", 1], ["deleteAtIndex", 1], ["get", 1]],
    },
    {
        "n": 4,
        "ops": [["MyLinkedList"], ["addAtHead", 1], ["addAtTail", 2], ["get", 0]],
    },
    {
        "n": 6,
        "ops": [["MyLinkedList"], ["addAtHead", 2], ["deleteAtIndex", 1],
                ["get", 0], ["addAtHead", 3], ["get", 0]],
    },
    {
        "n": 8,
        "ops": [["MyLinkedList"], ["addAtIndex", 0, 1], ["addAtIndex", 1, 2],
                ["addAtIndex", 2, 3], ["get", 0], ["get", 1], ["get", 2], ["get", 3]],
    },
    {
        "n": 7,
        "ops": [["MyLinkedList"], ["addAtHead", 1], ["addAtHead", 2],
                ["addAtHead", 3], ["get", 0], ["get", 1], ["get", 2]],
    },
    {
        "n": 6,
        "ops": [["MyLinkedList"], ["addAtTail", 1], ["addAtTail", 2],
                ["addAtTail", 3], ["deleteAtIndex", 1], ["get", 0], ["get", 1]],
    },
    {
        "n": 5,
        "ops": [["MyLinkedList"], ["get", 0], ["deleteAtIndex", 0],
                ["addAtHead", 5], ["get", 0]],
    },
    {
        "n": 10,
        "ops": [["MyLinkedList"], ["addAtHead", 4], ["addAtHead", 1],
                ["addAtTail", 5], ["addAtIndex", 1, 2], ["addAtIndex", 4, 3],
                ["get", 0], ["get", 1], ["get", 2], ["get", 3]],
    },
]


if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["n"], c["ops"])
        out.append({
            "id": i,
            "input": {"n": c["n"], "ops": c["ops"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
