import sys
import json

def solve(case_id: int) -> str:
    # Read all input lines
    data = sys.stdin.read()
    lines = data.strip().split('\n')
    
    # Find the case line
    target_prefix = f"CASE{case_id}="
    case_line = None
    for line in lines:
        if line.startswith(target_prefix):
            case_line = line[len(target_prefix):]
            break
    
    if case_line is None:
        return "False"
    
    # Parse pipe-separated values
    parts = case_line.split('|')
    # First part is N, second part is N, then the rooms data
    # Format: CASE0=N | N | k0 a0_1 ... | k1 a1_1 ... | ...
    # But based on example: "CASE0=3 | 3 | 3 1 2 0 1 0 0"
    # So: case_id value | N | all_keys_data
    
    # Actually looking at example more carefully:
    # CASE0=3 | 3 | 3 1 2 0 1 0 0
    # The first "3" is the case_id value, second "3" is N, then "3 1 2 0 1 0 0" is the rooms
    
    # Let's parse: skip first part (it's the case_id echo)
    n = int(parts[1].strip())
    
    # Concatenate remaining parts as the rooms data
    rooms_data = ' '.join(parts[2:])
    tokens = rooms_data.split()
    
    # Build adjacency list
    rooms = []
    idx = 0
    for i in range(n):
        if idx >= len(tokens):
            rooms.append([])
            continue
        k = int(tokens[idx])
        idx += 1
        keys = []
        for j in range(k):
            if idx < len(tokens):
                keys.append(int(tokens[idx]))
                idx += 1
        rooms.append(keys)
    
    # BFS from room 0
    visited = [False] * n
    visited[0] = True
    stack = [0]
    
    while stack:
        room = stack.pop()
        for key in rooms[room]:
            if not visited[key]:
                visited[key] = True
                stack.append(key)
    
    # Check if all visited
    if all(visited):
        return "True"
    else:
        return "False"


CASES = [
    {"case_id": 0},
    {"case_id": 1},
    {"case_id": 2},
    {"case_id": 3},
    {"case_id": 4},
]


def _build_input():
    """Build the CASE lines based on CASES."""
    lines = []
    # Test case 0: example from problem - all reachable
    lines.append("CASE0=3 | 3 | 3 1 2 0 1 0 0")
    # Test case 1: not all reachable - room 2 is isolated
    lines.append("CASE1=3 | 3 | 1 1 1 0 0 0")
    # Test case 2: single room, trivially reachable
    lines.append("CASE2=1 | 1 | 0")
    # Test case 3: N=2, room 0 has key to room 1, room 1 has key back to room 0
    lines.append("CASE3=2 | 2 | 1 1 1 0")
    # Test case 4: N=2, room 0 has no keys, can't reach room 1
    lines.append("CASE4=2 | 2 | 0 1 0")
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    # Save original stdin, provide our test input
    input_text = _build_input()
    sys.stdin = sys.__stdin__  # restore
    
    results = []
    for i, case in enumerate(CASES):
        cid = case["case_id"]
        # Run solve with proper stdin
        old_stdin = sys.stdin
        sys.stdin = type(sys.stdin).__class__(input_text) if False else sys.stdin
        # Just use io.StringIO
        import io
        sys.stdin = io.StringIO(input_text)
        result = solve(cid)
        sys.stdin = old_stdin
        results.append({
            "id": i,
            "input": {"case_id": cid},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
