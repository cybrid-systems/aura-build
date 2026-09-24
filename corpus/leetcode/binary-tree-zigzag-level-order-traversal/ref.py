import json
from collections import deque


def solve(root):
    """Compute zigzag level order traversal from a Lisp-style tree."""
    if root is None or root == 'NIL' or (isinstance(root, dict) and root.get('type') == 'NIL'):
        return {'type': 'NIL'}

    # Parse tree from various possible Lisp-style formats
    def parse_node(node):
        """Convert a parsed node into (value, left, right) form."""
        if node is None or node == 'NIL':
            return None
        if isinstance(node, dict):
            t = node.get('type')
            if t == 'ROOT':
                # root has children directly
                left = parse_node(node.get('left'))
                right = parse_node(node.get('right'))
                return (None, left, right)
            if t == 'NODE':
                val = node.get('val', 0)
                left = parse_node(node.get('left'))
                right = parse_node(node.get('right'))
                return (val, left, right)
            if t == 'VAL':
                return (node.get('val', 0), None, None)
            if t == 'LEFT':
                inner = parse_node(node.get('child'))
                return inner  # treat LEFT wrapper as its child
            if t == 'RIGHT':
                inner = parse_node(node.get('child'))
                return inner
        if isinstance(node, list):
            # [type, ...args]
            if not node:
                return None
            head = node[0]
            if head == 'ROOT':
                # (ROOT val left right) or (ROOT left right)
                if len(node) >= 4 and isinstance(node[1], (int, str)) and str(node[1]).lstrip('-').isdigit():
                    val = int(node[1])
                    left = parse_node(node[2]) if len(node) > 2 else None
                    right = parse_node(node[3]) if len(node) > 3 else None
                    return (val, left, right)
                else:
                    # (ROOT left right)
                    left = parse_node(node[1]) if len(node) > 1 else None
                    right = parse_node(node[2]) if len(node) > 2 else None
                    return (None, left, right)
            if head == 'NODE':
                # (NODE val left right) or (NODE (VAL n) (LEFT ...) (RIGHT ...))
                val = 0
                left = None
                right = None
                for arg in node[1:]:
                    if isinstance(arg, list) and len(arg) >= 1:
                        if arg[0] == 'VAL':
                            val = int(arg[1])
                        elif arg[0] == 'LEFT':
                            left = parse_node(arg[1] if len(arg) > 1 else None)
                        elif arg[0] == 'RIGHT':
                            right = parse_node(arg[1] if len(arg) > 1 else None)
                return (val, left, right)
            if head == 'VAL':
                return (int(node[1]), None, None)
        return None

    parsed = parse_node(root)
    if parsed is None:
        return {'type': 'NIL'}

    # BFS
    queue = deque([parsed])
    levels = []
    while queue:
        level_vals = []
        size = len(queue)
        for _ in range(size):
            val, left, right = queue.popleft()
            level_vals.append(val)
            if left is not None:
                queue.append(left)
            if right is not None:
                queue.append(right)
        levels.append(level_vals)

    # Zigzag: reverse odd-indexed levels (0-indexed)
    result = []
    for i, lvl in enumerate(levels):
        if i % 2 == 1:
            result.append(list(reversed(lvl)))
        else:
            result.append(list(lvl))

    return {'type': 'LEVEL', 'levels': result}


def to_output(obj):
    """Convert result to harness string format."""
    if obj.get('type') == 'NIL':
        return '(NIL)'
    if obj.get('type') == 'LEVEL':
        parts = []
        for lvl in obj['levels']:
            parts.append('(' + ' '.join(str(x) for x in lvl) + ')')
        return '(' + ' '.join(parts) + ')'
    return ''


CASES = [
    {'id': 0, 'root': None},
    {'id': 1, 'root': ['ROOT', ['VAL', 1]]},
    {'id': 2, 'root': ['ROOT', ['VAL', 3], ['VAL', 9], ['VAL', 20], ['NODE', ['VAL', 15]], ['NODE', ['VAL', 7]]]},
    {'id': 3, 'root': ['ROOT', ['VAL', 1], ['NODE', ['VAL', 2], ['NODE', ['VAL', 4]], ['NODE', ['VAL', 5]]], ['NODE', ['VAL', 3], ['NODE', ['VAL', 6]], ['NODE', ['VAL', 7]]]]},
    {'id': 4, 'root': ['ROOT', ['VAL', 1], ['VAL', 2]]},
    {'id': 5, 'root': ['ROOT', ['VAL', 1]]},
]


if __name__ == '__main__':
    out = []
    for case in CASES:
        result = solve(case['root'])
        out.append({
            'id': case['id'],
            'input': {'root': case['root']},
            'expected': json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
