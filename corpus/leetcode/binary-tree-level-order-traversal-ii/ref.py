import sys

def tokenize(s):
    tokens = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c in '()':
            tokens.append(c)
            i += 1
            continue
        if c.isdigit() or (c == '-' and i + 1 < len(s) and s[i+1].isdigit()):
            j = i + 1
            while j < len(s) and (s[j].isdigit() or s[j] == '-'):
                # careful: only consume leading minus; subsequent minuses shouldn't be part of number
                if s[j] == '-' and j > i:
                    break
                j += 1
            tokens.append(s[i:j])
            i = j
            continue
        i += 1
    return tokens

def parse(tokens, pos):
    if pos >= len(tokens):
        return None, pos
    tok = tokens[pos]
    if tok == 'nil':
        return None, pos + 1
    if tok == '(':
        # expect ( node VAL LEFT RIGHT )
        assert tokens[pos+1] == 'node', f"expected node at {pos+1}, got {tokens[pos+1]}"
        val = int(tokens[pos+2])
        left, pos = parse(tokens, pos+3)
        right, pos = parse(tokens, pos)
        assert tokens[pos] == ')', f"expected ) at {pos}, got {tokens[pos]}"
        node = {'val': val, 'left': left, 'right': right}
        return node, pos + 1
    return None, pos

def build_tree(s):
    s = s.strip()
    if s == 'nil' or s == '':
        return None
    tokens = tokenize(s)
    tree, _ = parse(tokens, 0)
    return tree

def level_order_bottom_up(root):
    if root is None:
        return []
    levels = []
    current = [root]
    while current:
        level_vals = [n['val'] for n in current]
        levels.append(level_vals)
        next_level = []
        for n in current:
            if n['left'] is not None:
                next_level.append(n['left'])
            if n['right'] is not None:
                next_level.append(n['right'])
        current = next_level
    levels.reverse()
    return levels

def format_levels(levels):
    if not levels:
        return '[]'
    parts = []
    for lvl in levels:
        inner = ' '.join(str(v) for v in lvl)
        parts.append(f'[{inner}]')
    return '[' + ' '.join(parts) + ']'

def solve(root):
    levels = level_order_bottom_up(root)
    return format_levels(levels)

CASES = [
    {'root': None},
    {'root': {'val': 1, 'left': None, 'right': None}},
    {'root': {'val': 3, 'left': {'val': 9, 'left': None, 'right': None}, 'right': {'val': 20, 'left': {'val': 15, 'left': None, 'right': None}, 'right': {'val': 7, 'left': None, 'right': None}}}},
    {'root': {'val': 1, 'left': {'val': 2, 'left': {'val': 4, 'left': None, 'right': None}, 'right': None}, 'right': {'val': 3, 'left': None, 'right': {'val': 5, 'left': None, 'right': None}}}},
    {'root': {'val': 1, 'left': {'val': 2, 'left': {'val': 3, 'left': None, 'right': None}, 'right': {'val': 4, 'left': None, 'right': None}}, 'right': {'val': 5, 'left': None, 'right': None}}},
    {'root': {'val': 0, 'left': {'val': -5, 'left': None, 'right': None}, 'right': {'val': 5, 'left': None, 'right': {'val': -10, 'left': None, 'right': None}}}},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(case['root'])
        results.append({"id": i, "input": {"root": case['root']}, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
