from typing import List, Optional, Dict, Any
import json


class Node:
    __slots__ = ("v", "l", "r")

    def __init__(self, v: int):
        self.v = v
        self.l: Optional["Node"] = None
        self.r: Optional["Node"] = None


def _empty() -> Node:
    return None  # type: ignore


def build_tree_from_env(env: Dict[str, str]) -> Optional[Node]:
    """Read environment to construct a tree according to the described convention."""
    if "ROOT" not in env:
        return None
    n = len(env)  # not exact; we discover by scanning keys
    # The number of nodes equals max index + 1. We need to find that.
    indices = set()
    for k in env:
        if k.startswith("L_") or k.startswith("R_") or k.startswith("NL_") or k.startswith("NR_"):
            # suffix is a number
            suffix = k.split("_", 1)[1]
            try:
                indices.add(int(suffix))
            except ValueError:
                pass
    # Also include root index 0
    indices.add(0)
    if not indices:
        return None
    total = max(indices) + 1
    nodes: List[Optional[Node]] = [None] * total
    # Create nodes by scanning indices from 0..total-1
    # We need node values for each index. Values come from ROOT (for index 0)
    # or possibly from NL/NR keys. But based on the spec, only ROOT is provided.
    # However, the example uses NL and NR for deeper nodes. Let's interpret: each
    # pair of child lines also implicitly defines a node value? Actually rereading:
    # "_NL* / _NR* are auxiliary lines used for nested nodes and follow the same
    # rules as _L / _R." That doesn't explicitly give values for inner nodes.
    # Perhaps the convention is that values are not separately given? That's odd.
    # Let's assume NL/NR carry the value of the node being defined. Actually the
    # original problem likely had separate value lines, but the prompt simplified
    # and only ROOT has a value. That means all node values must equal root value?
    # That doesn't make sense.
    #
    # Re-reading more carefully: "_ROOT is the root value (an integer)." It
    # doesn't say inner nodes have their own value lines. But then how do we know
    # their values? Perhaps in this encoding scheme, each child-line key like
    # CASE0_L or CASE0_NL also encodes the value of the child? The prompt says
    # "_L and _R are the child indices of the root". So they're indices, not
    # values.
    #
    # I suspect the actual intended encoding has separate value lines for each
    # node (like CASE0_V_0=10, CASE0_V_1=5, etc.) but the prompt simplified.
    # For safety, we'll only use ROOT for the root value, and all other nodes
    # default to 0. But that yields wrong answers in general.
    #
    # Actually, let's look at the example output: "((1 2) (1 3))" — this shows
    # paths with varying values 1,2,3, so multiple distinct node values exist.
    # The encoding MUST provide values per node. Given the prompt's ambiguity,
    # I'll adopt a flexible convention: if a key CASEi_V_k exists, use it;
    # otherwise, if k==0 use ROOT, else default to 0. This handles both cases.
    pass
    # Rebuild with better parsing
    nodes = [None] * total
    for i in range(total):
        v = None
        v_key = f"V_{i}"
        if v_key in env:
            try:
                v = int(env[v_key])
            except ValueError:
                v = 0
        elif i == 0:
            v = int(env["ROOT"])
        else:
            v = 0
        nodes[i] = Node(v)
    # Now link children
    for i in range(total):
        l_key = f"L_{i}"
        r_key = f"R_{i}"
        if l_key in env and env[l_key].strip() != "":
            ci = int(env[l_key])
            if 0 <= ci < total and nodes[ci] is not None:
                nodes[i].l = nodes[ci]  # type: ignore
        if r_key in env and env[r_key].strip() != "":
            ci = int(env[r_key])
            if 0 <= ci < total and nodes[ci] is not None:
                nodes[i].r = nodes[ci]  # type: ignore
    return nodes[0] if nodes else None


def solve(env: Dict[str, Any], target: int) -> List[List[int]]:
    """Compute all root-to-leaf paths summing to target.

    `env` is a dict mapping string keys to string values representing one CASE
    of the pre-encoded tree format described in the problem statement.
    """
    root = build_tree_from_env(env)
    result: List[List[int]] = []
    if root is None:
        return result

    def dfs(node: Optional[Node], remaining: int, path: List[int]) -> None:
        if node is None:
            return
        path.append(node.v)
        new_rem = remaining - node.v
        if node.l is None and node.r is None:
            if new_rem == 0:
                result.append(path.copy())
        else:
            dfs(node.l, new_rem, path)
            dfs(node.r, new_rem, path)
        path.pop()

    dfs(root, target, [])
    return result


# ---------- Test harness ----------
CASES = [
    # Case 0: empty tree
    {"env": {}, "target": 0},
    # Case 1: single root, leaf, matches target
    {"env": {"ROOT": "5"}, "target": 5},
    # Case 2: single root, leaf, does not match target
    {"env": {"ROOT": "5"}, "target": 1},
    # Case 3: root 10, left 5, right 15; left has children 3,7
    # Paths: 10->5->3 (sum 18), 10->5->7 (sum 22), 10->15 (sum 25)
    {"env": {"ROOT": "10", "L_0": "1", "R_0": "2", "V_0": "10",
             "V_1": "5", "V_2": "15", "V_3": "3", "V_4": "7",
             "L_1": "3", "R_1": "4", "L_2": "", "R_2": ""}, "target": 22},
    # Case 4: negative values
    # Tree: root=-2, left=-3, right=2; left has right child=1; right has left=-1, right=3
    # Leaves: -2->-3->1 (sum -4), -2->2->-1 (sum -1), -2->2->3 (sum 3)
    {"env": {"ROOT": "-2", "L_0": "1", "R_0": "2", "V_0": "-2",
             "V_1": "-3", "V_2": "2", "V_3": "1", "V_4": "-1", "V_5": "3",
             "L_1": "", "R_1": "3", "L_2": "4", "R_2": "5"}, "target": -1},
    # Case 5: zero values, multiple matching paths
    # root=0, left=0, right=0; both leaves are 0
    {"env": {"ROOT": "0", "L_0": "1", "R_0": "2", "V_0": "0",
             "V_1": "0", "V_2": "0", "L_1": "", "R_1": "", "L_2": "", "R_2": ""}, "target": 0},
    # Case 6: deeper tree
    # root=1, left=2, right=3; left has left=4, right=5; right has left=6, right=7
    # Leaves: 1->2->4 (sum 7), 1->2->5 (sum 8), 1->3->6 (sum 10), 1->3->7 (sum 11)
    {"env": {"ROOT": "1", "L_0": "1", "R_0": "2", "V_0": "1",
             "V_1": "2", "V_2": "3", "V_3": "4", "V_4": "5", "V_5": "6", "V_6": "7",
             "L_1": "3", "R_1": "4", "L_2": "5", "R_2": "6",
             "L_3": "", "R_3": "", "L_4": "", "R_4": "", "L_5": "", "R_5": "", "L_6": "", "R_6": ""},
     "target": 7},
    # Case 7: all nodes negative, no matching path
    {"env": {"ROOT": "-1", "L_0": "1", "R_0": "2", "V_0": "-1",
             "V_1": "-2", "V_2": "-3", "L_1": "", "R_1": "", "L_2": "", "R_2": ""}, "target": 0},
]


def _to_jsonable(obj):
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, str):
        return obj
    return obj


if __name__ == "__main__":
    out = []
    for i, case in enumerate(CASES):
        env = case["env"]
        target = case["target"]
        result = solve(env, target)
        # canonical form: sort paths lexicographically so output is deterministic
        canonical = sorted([list(p) for p in result])
        out.append({
            "id": i,
            "input": {"env": env, "target": target},
            "expected": json.dumps(canonical, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
