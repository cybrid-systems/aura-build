import sys, json

class MyCircularDeque:
    def __init__(self, k: int):
        self.cap = k
        self.buf = [0] * k
        self.head = 0  # index of front element
        self.count = 0  # number of elements

    def _wrap(self, i):
        return i % self.cap

    def insertFront(self, value: int) -> bool:
        if self.isFull():
            return False
        # front goes to (head - 1) mod cap
        self.head = self._wrap(self.head - 1)
        self.buf[self.head] = value
        self.count += 1
        return True

    def insertLast(self, value: int) -> bool:
        if self.isFull():
            return False
        tail = self._wrap(self.head + self.count)
        self.buf[tail] = value
        self.count += 1
        return True

    def deleteFront(self) -> int:
        if self.isEmpty():
            return -1
        val = self.buf[self.head]
        self.head = self._wrap(self.head + 1)
        self.count -= 1
        return val

    def deleteLast(self) -> int:
        if self.isEmpty():
            return -1
        last_idx = self._wrap(self.head + self.count - 1)
        val = self.buf[last_idx]
        self.count -= 1
        return val

    def getFront(self) -> int:
        if self.isEmpty():
            return -1
        return self.buf[self.head]

    def getRear(self) -> int:
        if self.isEmpty():
            return -1
        last_idx = self._wrap(self.head + self.count - 1)
        return self.buf[last_idx]

    def isEmpty(self) -> bool:
        return self.count == 0

    def isFull(self) -> bool:
        return self.count == self.cap


def run_operations(k, operations):
    dq = MyCircularDeque(k)
    results = []
    i = 0
    while i < len(operations):
        op = operations[i]
        if op == "insertFront":
            v = int(operations[i + 1])
            results.append(dq.insertFront(v))
            i += 2
        elif op == "insertLast":
            v = int(operations[i + 1])
            results.append(dq.insertLast(v))
            i += 2
        elif op == "deleteFront":
            results.append(dq.deleteFront())
            i += 1
        elif op == "deleteLast":
            results.append(dq.deleteLast())
            i += 1
        elif op == "getFront":
            results.append(dq.getFront())
            i += 1
        elif op == "getRear":
            results.append(dq.getRear())
            i += 1
        elif op == "isEmpty":
            results.append(dq.isEmpty())
            i += 1
        elif op == "isFull":
            results.append(dq.isFull())
            i += 1
        else:
            # unknown op, skip
            i += 1
    return results


def solve(k, operations):
    return run_operations(k, operations)


CASES = [
    {
        "id": 0,
        "input": {
            "k": 3,
            "operations": [
                "insertLast", "1",
                "insertLast", "2",
                "insertFront", "3",
                "insertFront", "4",
                "getRear",
                "isFull",
                "deleteLast",
                "insertFront", "4",
                "getFront"
            ]
        }
    },
    {
        "id": 1,
        "input": {
            "k": 1,
            "operations": [
                "insertLast", "10",
                "getFront",
                "getRear",
                "isFull",
                "deleteLast",
                "isEmpty",
                "insertFront", "20",
                "getFront",
                "insertLast", "30"
            ]
        }
    },
    {
        "id": 2,
        "input": {
            "k": 4,
            "operations": [
                "isEmpty",
                "insertFront", "1",
                "insertLast", "2",
                "getFront",
                "getRear",
                "deleteFront",
                "deleteLast",
                "isEmpty",
                "isFull"
            ]
        }
    },
    {
        "id": 3,
        "input": {
            "k": 2,
            "operations": [
                "insertFront", "1",
                "insertLast", "2",
                "insertFront", "3",
                "getFront",
                "getRear",
                "isFull",
                "deleteFront",
                "deleteLast",
                "deleteFront",
                "isEmpty"
            ]
        }
    },
    {
        "id": 4,
        "input": {
            "k": 5,
            "operations": [
                "insertLast", "1",
                "insertLast", "2",
                "insertLast", "3",
                "insertLast", "4",
                "deleteFront",
                "deleteLast",
                "getFront",
                "getRear",
                "insertFront", "0",
                "insertLast", "5",
                "isFull",
                "getRear",
                "deleteFront",
                "deleteLast"
            ]
        }
    },
    {
        "id": 5,
        "input": {
            "k": 3,
            "operations": [
                "getFront",
                "getRear",
                "deleteFront",
                "deleteLast",
                "isEmpty",
                "isFull"
            ]
        }
    }
]


if __name__ == "__main__":
    out = []
    for case in CASES:
        inp = case["input"]
        result = solve(inp["k"], inp["operations"])
        out.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
