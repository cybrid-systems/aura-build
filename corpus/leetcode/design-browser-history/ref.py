import json

class _Node:
    __slots__ = ("url", "prev", "next")
    def __init__(self, url, prev=None, next_=None):
        self.url = url
        self.prev = prev
        self.next = next_

class BrowserHistory:
    def __init__(self, homepage: str):
        self.cur = _Node(homepage)

    def visit(self, url: str) -> None:
        node = _Node(url, prev=self.cur)
        self.cur.next = node
        self.cur = node

    def back(self, steps: int) -> str:
        i = 0
        while i < steps and self.cur.prev is not None:
            self.cur = self.cur.prev
            i += 1
        return self.cur.url

    def forward(self, steps: int) -> str:
        i = 0
        while i < steps and self.cur.next is not None:
            self.cur = self.cur.next
            i += 1
        return self.cur.url

def run_case(case: dict) -> dict:
    ops = case["operations"]
    outputs = []
    history = None
    for op in ops:
        kind = op[0]
        if kind == "Visit":
            if history is None:
                history = BrowserHistory(op[1])
            else:
                history.visit(op[1])
        elif kind == "Back":
            outputs.append(history.back(int(op[1])))
        elif kind == "Forward":
            outputs.append(history.forward(int(op[1])))
    return {"outputs": outputs}

CASES = [
    {
        "operations": [
            ["Visit", "leetcode.com"],
            ["Visit", "google.com"],
            ["Visit", "facebook.com"],
            ["Visit", "youtube.com"],
            ["Back", "1"],
            ["Back", "1"],
            ["Forward", "1"],
            ["Visit", "linkedin.com"],
            ["Forward", "2"],
            ["Back", "2"],
            ["Back", "7"],
        ]
    },
    {
        "operations": [
            ["Visit", "home.io"],
            ["Back", "3"],
            ["Forward", "5"],
        ]
    },
    {
        "operations": [
            ["Visit", "a.com"],
            ["Visit", "b.com"],
            ["Visit", "c.com"],
            ["Forward", "2"],
            ["Back", "2"],
            ["Visit", "d.com"],
            ["Forward", "1"],
            ["Back", "1"],
            ["Back", "1"],
            ["Forward", "3"],
        ]
    },
    {
        "operations": [
            ["Visit", "root"],
            ["Visit", "p1"],
            ["Visit", "p2"],
            ["Visit", "p3"],
            ["Back", "1"],
            ["Visit", "p4"],
            ["Forward", "10"],
            ["Back", "10"],
        ]
    },
    {
        "operations": [
            ["Visit", "x"],
            ["Visit", "y"],
            ["Back", "1"],
            ["Back", "1"],
            ["Back", "1"],
            ["Forward", "1"],
            ["Visit", "z"],
            ["Forward", "1"],
            ["Back", "1"],
        ]
    },
]

def solve():
    results = []
    for i, case in enumerate(CASES):
        out = run_case(case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(",", ":"), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))

if __name__ == "__main__":
    solve()
