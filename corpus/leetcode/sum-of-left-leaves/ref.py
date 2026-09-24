import os
import sys
import json


def parse_tokens(raw):
    """Parse token string into a tree and return (root, leftover_tokens).
    Tokens are produced by splitting the raw string on parentheses/spaces.
    Each token starting with '(' is an opening paren, then the next token is the value.
    """
    tokens = raw.split()
    pos = [0]

    def parse():
        if pos[0] >= len(tokens):
            return None
        tok = tokens[pos[0]]
        pos[0] += 1
        if tok == '(':
            # next token is the value
            if pos[0] >= len(tokens):
                return None
            val_tok = tokens[pos[0]]
            pos[0] += 1
            if val_tok == 'nil':
                return None
            # recursively parse left and right until closing paren
            left = parse()
            right = parse()
            # consume closing paren ')' if present
            if pos[0] < len(tokens) and tokens[pos[0]] == ')':
                pos[0] += 1
            return (val_tok, left, right)
        elif tok == 'nil':
            return None
        elif tok == ')':
            return None
        else:
            # standalone value token (shouldn't happen at top level)
            return (tok, None, None)

    root = parse()
    return root


def solve(root):
    """Sum of left leaves. root is either None or (value, left, right)."""
    if root is None:
        return 0
    # Unpack - root might be a string value if built differently, but our parser
    # produces tuple (val, left, right)
    if isinstance(root, tuple):
        _, left, right = root
    else:
        return 0

    total = 0
    if left is not None and isinstance(left, tuple):
        _, ll, lr = left
        if ll is None and lr is None:
            # left child is a leaf
            total += int(left[0])
        else:
            total += solve(left)
    if right is not None:
        total += solve(right)
    return total


# -------------------- Test harness --------------------

def build_case(values, lefts, rights):
    """Build a tree from serialized components - placeholder, unused."""
    pass


CASES = [
    {
        "id": 0,
        # Tree:   3
        #        / \
        #       2   2
        #          / \
        #         5   6
        # Left leaves: 2 and 5  -> sum = 7
        "raw": "( 3 ( 2 ( nil nil ) ( nil nil ) ) ( 2 ( 5 ( nil nil ) ( nil nil ) ) ( 6 ( nil nil ) ( nil nil ) ) ) )"
    },
    {
        "id": 1,
        # Tree:   1
        #        / \
        #       2   3
        # Left leaves: 2 -> sum = 2
        "raw": "( 1 ( 2 ( nil nil ) ( nil nil ) ) ( 3 ( nil nil ) ( nil nil ) ) )"
    },
    {
        "id": 2,
        # Empty tree
        "raw": "nil"
    },
    {
        "id": 3,
        # Single node leaf (treated as root with no children -> not a left leaf)
        "raw": "( 7 ( nil nil ) ( nil nil ) )"
    },
    {
        "id": 4,
        # Tree where right has a left leaf deep:
        #        1
        #         \
        #          2
        #         /
        #        4
        # Left leaves: 4
        "raw": "( 1 ( nil nil ) ( 2 ( 4 ( nil nil ) ( nil nil ) ) ( nil nil ) ) )"
    },
    {
        "id": 5,
        # Larger tree:
        #         10
        #        /  \
        #       5    15
        #      / \     \
        #     3   7     20
        # Left leaves: 3, 7 -> sum=10
        "raw": "( 10 ( 5 ( 3 ( nil nil ) ( nil nil ) ) ( 7 ( nil nil ) ( nil nil ) ) ) ( 15 ( nil nil ) ( 20 ( nil nil ) ( nil nil ) ) ) )"
    },
]


def _normalize(root):
    """Convert the (str, ...) tuple tree into (int, ...) tuple tree."""
    if root is None:
        return None
    val, left, right = root
    return (int(val), _normalize(left), _normalize(right))


if __name__ == '__main__':
    results = []
    for case in CASES:
        root_raw = parse_tokens(case["raw"])
        root = _normalize(root_raw)
        ans = solve(root)
        results.append({
            "id": case["id"],
            "input": {"raw": case["raw"]},
            "expected": json.dumps(ans, separators=(',', ':'), ensure_ascii=False)
        })

    # Also handle the live env-variable case if present
    env_root = None
    for k, v in os.environ.items():
        if k.startswith("CASE") and v:
            env_root = v
            break
    if env_root is not None:
        parsed = parse_tokens(env_root)
        normalized = _normalize(parsed)
        out = solve(normalized)
        sys.stdout.write(str(out) + "nil")
    else:
        sys.stdout.write(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
