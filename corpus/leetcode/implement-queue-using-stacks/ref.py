import sys
import json

class MyQueue:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def enqueue(self, x):
        self.in_stack.append(x)

    def _transfer(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())

    def dequeue(self):
        if self.empty():
            raise IndexError("dequeue from empty queue")
        self._transfer()
        return self.out_stack.pop()

    def peek(self):
        if self.empty():
            raise IndexError("peek from empty queue")
        self._transfer()
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack


def solve(input_data=None):
    if input_data is None:
        data = sys.stdin.read()
    else:
        data = input_data

    lines = data.splitlines()
    q = MyQueue()
    results = []

    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue
        cmd = parts[0].upper()
        if cmd == "ENQUEUE":
            q.enqueue(int(parts[1]))
        elif cmd == "DEQUEUE":
            try:
                results.append(str(q.dequeue()))
            except IndexError:
                results.append("ERROR")
        elif cmd == "PEEK":
            try:
                results.append(str(q.peek()))
            except IndexError:
                results.append("ERROR")
        elif cmd == "EMPTY":
            results.append("TRUE" if q.empty() else "FALSE")
        else:
            results.append("ERROR")

    return results


CASES = [
    {
        "input": "ENQUEUE 1\nENQUEUE 2\nENQUEUE 3\nDEQUEUE\nPEEK\nEMPTY\n"
    },
    {
        "input": "DEQUEUE\nPEEK\nEMPTY\n"
    },
    {
        "input": "ENQUEUE 10\nENQUEUE 20\nENQUEUE 30\nENQUEUE 40\nDEQUEUE\nDEQUEUE\nDEQUEUE\nDEQUEUE\nDEQUEUE\n"
    },
    {
        "input": "ENQUEUE 5\nENQUEUE 6\nPEEK\nDEQUEUE\nENQUEUE 7\nPEEK\nDEQUEUE\nDEQUEUE\nEMPTY\n"
    },
    {
        "input": "ENQUEUE 1\nDEQUEUE\nENQUEUE 2\nENQUEUE 3\nPEEK\nEMPTY\nDEQUEUE\nDEQUEUE\nDEQUEUE\n"
    },
    {
        "input": "ENQUEUE 100\nENQUEUE 200\nDEQUEUE\nENQUEUE 300\nPEEK\nDEQUEUE\nPEEK\nDEQUEUE\nDEQUEUE\nEMPTY\n"
    },
    {
        "input": ""
    },
    {
        "input": "ENQUEUE -1\nENQUEUE -2\nENQUEUE -3\nDEQUEUE\nDEQUEUE\nDEQUEUE\nDEQUEUE\nEMPTY\n"
    },
]


if __name__ == "__main__":
    output = []
    for i, case in enumerate(CASES):
        result = solve(case["input"])
        output.append({
            "id": i,
            "input": case["input"],
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
