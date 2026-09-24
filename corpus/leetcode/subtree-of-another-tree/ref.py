import json, os, re

def parse(s):
    s = s.strip()
    if s == '()':
        return None
    # Parse (val left right)
    # find first space
    assert s[0] == '(' and s[-1] == ')'
    inner = s[1:-1]
    # split val, left, right at top level
    parts = []
    depth = 0
    cur = []
    for ch in inner:
        if ch == '(':
            depth += 1
            cur.append(ch)
        elif ch == ')':
            depth -= 1
            cur.append(ch)
        elif ch.isspace() and depth == 0:
            parts.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append(''.join(cur))
    val = int(parts[0])
    left = parse(parts[1])
    right = parse(parts[2])
    return {'val': val, 'left': left, 'right': right}

def is_same(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    return (a['val'] == b['val']
            and is_same(a['left'], b['left'])
            and is_same(a['right'], b['right']))

def is_subtree(root, sub):
    if sub is None:
        return True
    if root is None:
        return False
    if is_same(root, sub):
        return True
    return is_subtree(root['left'], sub) or is_subtree(root['right'], sub)

def solve(root, sub):
    return is_subtree(root, sub)

def parse_input(s):
    # (solve <root> <sub>)
    s = s.strip()
    assert s.startswith('(') and s.endswith(')')
    inner = s[1:-1]
    # split into two top-level
    parts = []
    depth = 0
    cur = []
    for ch in inner:
        if ch == '(':
            depth += 1
            cur.append(ch)
        elif ch == ')':
            depth -= 1
            cur.append(ch)
        elif ch.isspace() and depth == 0:
            parts.append(''.join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append(''.join(cur))
    assert parts[0] == 'solve'
    root = parse(parts[1])
    sub = parse(parts[2])
    return root, sub

CASES = [
    {'CASE0': '(solve (3 (4 (1 () ()) (2 () ())) (5 () ())) (4 (1 () ()) (2 () ())))'},
    {'CASE0': '(solve (3 (4 (1 () ()) (2 () (0 () ()))) (5 () ())) (4 (1 () ()) (2 () ())))'},
    {'CASE0': '(solve (1 (2 () ()) (3 () ())) ())'},
    {'CASE0': '(solve () ())'},
    {'CASE0': '(solve () (1 () ()))'},
    {'CASE0': '(solve (1 () (2 () (3 () ()))) (3 () ()))'},
    {'CASE0': '(solve (1 () (2 () ())) (2 () (3 () ())))'},
    {'CASE0': '(solve (1 (2 () ()) ()) (1 () (2 () ())))'},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        root, sub = parse_input(case['CASE0'])
        out = solve(root, sub)
        results.append({'id': i, 'input': case, 'expected': json.dumps(out, ensure_ascii=False)})
    print(json.dumps(results, ensure_ascii=False))
