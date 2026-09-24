import sys
import json

def solve(root):
    if root is None:
        return 0
    node = root.deref() if hasattr(root, 'deref') else root
    left = node.get(':left') if isinstance(node, dict) else getattr(node, '_left', None)
    right = node.get(':right') if isinstance(node, dict) else getattr(node, '_right', None)
    return 1 + max(solve(left), solve(right))


class Node:
    def __init__(self, left=None, right=None):
        self._left = left
        self._right = right

    def deref(self):
        return {':left': self._left, ':right': self._right}


def make_node(left=None, right=None):
    return Node(left, right)


CASES = [
    {'root': None},
    {'root': make_node()},
    {'root': make_node(make_node(), make_node())},
    {'root': make_node(make_node(make_node()), None)},
    {'root': make_node(None, make_node(None, make_node(None, make_node())))},
    {'root': make_node(make_node(make_node()), make_node(make_node()))},
    {'root': make_node(make_node(None, make_node()), make_node())},
    {'root': make_node(make_node(make_node(None, make_node())), None)},
]


def _to_input(case):
    return {'root': repr(case['root'])}


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case['root'])
        results.append({
            'id': i,
            'input': _to_input(case),
            'expected': json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
