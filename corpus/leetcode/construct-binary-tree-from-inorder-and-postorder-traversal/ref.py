import sys, json
from collections import deque

NULL_SENTINEL = 'null'

def parse_line(line):
    # Line format: CASE0_INORDER=[...] or CASE0_POSTORDER=[...]
    idx = line.find('[')
    arr_str = line[idx:-1]  # drop trailing newline; ends with ']'
    # strip outer brackets
    inner = arr_str.strip()[1:-1].strip()
    if not inner:
        return []
    parts = [p.strip() for p in inner.split(',')]
    result = []
    for p in parts:
        if p == NULL_SENTINEL or p == '-1' or p == 'None':
            result.append(None)
        else:
            try:
                result.append(int(p))
            except ValueError:
                result.append(None)
    return result

def build(inorder, postorder):
    if not inorder or not postorder:
        return None
    # Map value -> index in inorder
    idx_map = {v: i for i, v in enumerate(inorder) if v is not None}

    def helper(in_l, in_r, post_l, post_r):
        if in_l > in_r or post_l > post_r:
            return None
        root_val = postorder[post_r]
        if root_val is None:
            return None
        root = {'val': root_val, 'left': None, 'right': None}
        # find root in inorder
        try:
            root_in_idx = idx_map[root_val]
        except KeyError:
            return None
        left_size = root_in_idx - in_l
        root['left'] = helper(in_l, root_in_idx - 1, post_l, post_l + left_size - 1)
        root['right'] = helper(root_in_idx + 1, in_r, post_l + left_size, post_r - 1)
        return root

    return helper(0, len(inorder) - 1, 0, len(postorder) - 1)

def serialize(root):
    if root is None:
        return []
    result = []
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            result.append(None)
        else:
            result.append(node['val'])
            queue.append(node['left'])
            queue.append(node['right'])
    # trim trailing Nones
    while result and result[-1] is None:
        result.pop()
    return result

def solve(inorder_raw, postorder_raw):
    inorder = parse_line(inorder_raw)
    postorder = parse_line(postorder_raw)
    tree = build(inorder, postorder)
    out = serialize(tree)
    # Format with null sentinel
    parts = [NULL_SENTINEL if v is None else str(v) for v in out]
    print(f"RESULT=[{', '.join(parts)}]")

CASES = [
    {
        'inorder_raw': 'CASE0_INORDER=[1, 2, 3, null, 5]',
        'postorder_raw': 'CASE0_POSTORDER=[1, 3, null, 5, 2]',
    },
    {
        'inorder_raw': 'CASE0_INORDER=[1]',
        'postorder_raw': 'CASE0_POSTORDER=[1]',
    },
    {
        'inorder_raw': 'CASE0_INORDER=[]',
        'postorder_raw': 'CASE0_POSTORDER=[]',
    },
    {
        'inorder_raw': 'CASE0_INORDER=[2, 1, 3]',
        'postorder_raw': 'CASE0_POSTORDER=[2, 3, 1]',
    },
    {
        'inorder_raw': 'CASE0_INORDER=[4, 2, 5, 1, 6, 3, 7]',
        'postorder_raw': 'CASE0_POSTORDER=[4, 5, 2, 6, 7, 3, 1]',
    },
    {
        'inorder_raw': 'CASE0_INORDER=[null, 1, 2, 3]',
        'postorder_raw': 'CASE0_POSTORDER=[1, 3, 2, null]',
    },
    {
        'inorder_raw': 'CASE0_INORDER=[9, 3, 15, 20, 7]',
        'postorder_raw': 'CASE0_POSTORDER=[9, 15, 7, 20, 3]',
    },
]

if __name__ == '__main__':
    out_cases = []
    for i, case in enumerate(CASES):
        expected_parts = []
        # run solve to capture stdout
        import io
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            solve(case['inorder_raw'], case['postorder_raw'])
        finally:
            sys.stdout = old_stdout
        result = buf.getvalue().strip()
        expected_parts.append(result)
        out_cases.append({
            'id': i,
            'input': {
                'inorder_raw': case['inorder_raw'],
                'postorder_raw': case['postorder_raw'],
            },
            'expected': result,
        })
    print(json.dumps(out_cases, separators=(',', ':'), ensure_ascii=False))
