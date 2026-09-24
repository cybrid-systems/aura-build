import sys
import json

def solve(nodes: dict, child: dict) -> list:
    """
    nodes[id] = {"next": id | None, "prev": id | None}
    child[id] = id | None   # head of the child sublist, or None
    Returns: list of node ids in depth-first preorder.
    """
    # Find head: the node whose prev is None
    head = None
    for nid, info in nodes.items():
        if info["prev"] is None:
            head = nid
            break
    
    if head is None:
        return []
    
    result = []
    stack = [head]
    visited = set()
    
    while stack:
        node = stack.pop()
        if node is None or node in visited:
            continue
        visited.add(node)
        result.append(node)
        
        # Push next first, then child, so child is processed first (LIFO)
        # But we want: node, then child sublist, then next sibling
        # So push next first (it will be popped later), then push child (popped first)
        info = nodes[node]
        nxt = info["next"]
        chd = child.get(node)
        
        if nxt is not None:
            stack.append(nxt)
        if chd is not None:
            stack.append(chd)
    
    return result


def parse_input(text):
    """Parse the structured input into cases."""
    cases = []
    current_case = None
    
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith("CASE"):
            # CASE0=n
            case_idx = int(line.split("=")[1])
            if current_case is not None:
                cases.append(current_case)
            current_case = {
                "id": case_idx,
                "nodes": {},
                "child": {},
            }
        elif line.startswith("NODE"):
            # NODE0=id type
            parts = line.split("=", 1)[1].split()
            nid = int(parts[0])
            if current_case is not None:
                if nid not in current_case["nodes"]:
                    current_case["nodes"][nid] = {"next": None, "prev": None}
                current_case["child"].setdefault(nid, None)
        elif line.startswith("NEXT="):
            parts = line.split("=", 1)[1].split()
            frm, to = int(parts[0]), int(parts[1])
            if current_case is not None:
                current_case["nodes"].setdefault(frm, {"next": None, "prev": None})
                current_case["nodes"].setdefault(to, {"next": None, "prev": None})
                current_case["nodes"][frm]["next"] = to
                current_case["child"].setdefault(frm, None)
                current_case["child"].setdefault(to, None)
        elif line.startswith("PREV="):
            parts = line.split("=", 1)[1].split()
            frm, to = int(parts[0]), int(parts[1])
            if current_case is not None:
                current_case["nodes"].setdefault(frm, {"next": None, "prev": None})
                current_case["nodes"].setdefault(to, {"next": None, "prev": None})
                current_case["nodes"][frm]["prev"] = to
                current_case["child"].setdefault(frm, None)
                current_case["child"].setdefault(to, None)
        elif line.startswith("CHILD="):
            parts = line.split("=", 1)[1].split()
            frm, to = int(parts[0]), int(parts[1])
            if current_case is not None:
                current_case["nodes"].setdefault(frm, {"next": None, "prev": None})
                current_case["nodes"].setdefault(to, {"next": None, "prev": None})
                current_case["child"][frm] = to
        elif line.startswith("IDLIST="):
            # End of current case
            pass
    
    if current_case is not None:
        cases.append(current_case)
    
    return cases


CASES = []


if __name__ == '__main__':
    # Use the example from the problem as a test case
    example = """CASE0=0
NODE0=1 val
NODE0=2 val
NODE0=3 val
NODE0=4 val
NODE0=5 val
NODE0=6 val
NEXT=1 2
NEXT=2 3
NEXT=3 4
NEXT=4 5
NEXT=5 6
PREV=2 1
PREV=3 2
PREV=4 3
PREV=5 4
PREV=6 5
CHILD=3 7
NODE0=7 val
NEXT=7 8
NEXT=8 9
NEXT=9 10
PREV=8 7
PREV=9 8
PREV=10 9
CHILD=8 11
NODE0=11 val
NODE0=12 val
NEXT=11 12
PREV=12 11
IDLIST="""
    
    cases = parse_input(example)
    
    results = []
    for c in cases:
        res = solve(c["nodes"], c["child"])
        results.append({
            "id": c["id"],
            "input": {
                "nodes": {k: {"next": v["next"], "prev": v["prev"]} for k, v in c["nodes"].items()},
                "child": dict(c["child"])
            },
            "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)
        })
    
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
