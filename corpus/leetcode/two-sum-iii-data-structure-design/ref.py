import sys
import json

def solve(operations):
    """Process a list of operations and return results of :find operations.
    
    Args:
        operations: list of (op, value) tuples where op is 'add' or 'find'
    
    Returns:
        list of bool results for each :find operation
    """
    counts = {}
    results = []
    for op, val in operations:
        if op == 'add':
            counts[val] = counts.get(val, 0) + 1
        elif op == 'find':
            v = val
            found = False
            for x, c in counts.items():
                y = v - x
                if y not in counts:
                    continue
                if x == y:
                    if c >= 2:
                        found = True
                        break
                else:
                    found = True
                    break
            results.append(found)
    return results


def parse_input(text):
    """Parse CASE lines into operations."""
    operations = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: ":add 1" or ":find 4"
        if line.startswith(':add '):
            n = int(line[5:])
            operations.append(('add', n))
        elif line.startswith(':find '):
            v = int(line[6:])
            operations.append(('find', v))
    return operations


CASES = [
    {
        "description": "Basic example from prompt",
        "ops": [('add', 1), ('add', 3), ('add', 5), ('find', 4), ('find', 7)],
    },
    {
        "description": "Zeros pair with itself",
        "ops": [('add', 0), ('add', 0), ('find', 0)],
    },
    {
        "description": "No finds",
        "ops": [('add', 1), ('add', 2), ('add', 3)],
    },
    {
        "description": "Single element cannot pair with itself",
        "ops": [('add', 5), ('find', 10)],
    },
    {
        "description": "Negative numbers",
        "ops": [('add', -1), ('add', -3), ('add', 5), ('find', -4), ('find', 4)],
    },
    {
        "description": "Pair with itself after multiple adds",
        "ops": [('add', 2), ('add', 2), ('add', 3), ('find', 4), ('find', 6)],
    },
    {
        "description": "Empty structure",
        "ops": [('find', 0)],
    },
    {
        "description": "Find before add should not use later values",
        "ops": [('add', 1), ('find', 2), ('add', 1), ('find', 2)],
    },
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        ops = case['ops']
        out = solve(ops)
        # Convert bools to "true"/"false" strings matching expected stdout
        canonical = '\n'.join('true' if x else 'false' for x in out)
        results.append({
            "id": i,
            "input": {"ops": [list(o) for o in ops]},
            "expected": canonical,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
