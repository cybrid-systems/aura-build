import json
import sys
from io import StringIO


def solve(prices: list[int]) -> list[int]:
    """
    Compute the stock span for each day using a monotonic decreasing stack.
    The stack stores pairs of (price, span). We pop entries with price <= current
    price, summing their spans to extend today's span.
    """
    spans: list[int] = []
    # Stack holds pairs (price, span) in strictly decreasing order of price
    stack: list[tuple[int, int]] = []
    for price in prices:
        # Today's span starts at 1 (the day itself)
        span = 1
        # Pop all days with price <= today's price, merging their spans
        while stack and stack[-1][0] <= price:
            _, prev_span = stack.pop()
            span += prev_span
        stack.append((price, span))
        spans.append(span)
    return spans


CASES = [
    # Classic example from the problem
    {"prices": [100, 80, 60, 70, 60, 75]},
    # Single day
    {"prices": [42]},
    # Strictly decreasing prices -> every span is 1
    {"prices": [10, 9, 8, 7, 6]},
    # Strictly increasing prices -> spans are 1, 2, 3, ...
    {"prices": [1, 2, 3, 4, 5]},
    # Equal prices (condition is <= so equal days also merge)
    {"prices": [5, 5, 5, 5]},
    # Mix of increases and decreases
    {"prices": [3, 1, 2, 1, 4, 1]},
    # Two elements, decreasing
    {"prices": [10, 5]},
    # Two elements, increasing
    {"prices": [5, 10]},
]


def _run_io(prices: list[int]) -> list[int]:
    """Helper: run the original stdin/stdout form for parity."""
    buf_in = StringIO()
    buf_in.write(f"{len(prices)}\n")
    buf_in.write(" ".join(str(p) for p in prices) + "\n")
    old_stdin, old_stdout = sys.stdin, sys.stdout
    try:
        sys.stdin = StringIO(buf_in.getvalue())
        sys.stdout = StringIO()
        # Ingest from stdin just like the real judge would
        data = sys.stdin.read().split()
        n = int(data[0])
        arr = list(map(int, data[1:1 + n]))
        out = solve(arr)
        sys.stdout.write(" ".join(str(x) for x in out))
        return sys.stdout.getvalue().split()
    finally:
        sys.stdin, sys.stdout = old_stdin, old_stdout


if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        prices = case["prices"]
        result = solve(prices)
        # Canonicalize: space-joined integers string
        canonical = "[" + ",".join(str(x) for x in result) + "]"
        # Also verify the stdin/stdout form produces the same answer
        io_form = _run_io(prices)
        assert io_form == [str(x) for x in result], (io_form, result)
        results.append({
            "id": i,
            "input": {"prices": prices},
            "expected": canonical,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
