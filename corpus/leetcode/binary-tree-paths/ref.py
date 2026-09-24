import json
import sys
from typing import List, Optional, Dict, Any

def solve(root: Optional[Dict[str, Any]]) -> List[str]:
    if root is None:
        return []
    result = []
    def dfs(node, path):
        path = path + [str(node['val'])]
        if node['left'] is None and node['right'] is None:
            result.append('->'.join(path))
            return
        if node['left'] is not None:
            dfs(node['left'], path)
        if node['right'] is not None:
            dfs(node['right'], path)
    dfs(root, [])
    return result

def build_tree(arr: List[Optional[int]]) -> Optional[Dict[str, Any]]:
    if not arr:
        return None
    nodes = [None if v is None else {'val': v, 'left': None, 'right': None} for v in arr]
    kids = nodes[::-1]
    root = kids.pop()
    for node in nodes:
        if node is not None:
            if kids:
                node['left'] = kids.pop()
            if kids:
                node['right'] = kids.pop()
    return root

CASES = [
    {'root': build_tree([1,2,3,None,5])},
    {'root': build_tree([1])},
    {'root': build_tree([])},
    {'root': build_tree([1,2,3,4,5,6,7])},
    {'root': build_tree([1,2,None,3,None,4,None,5])},
    {'root': build_tree([10,5,15,3,7,12,20])},
    {'root': build_tree([1,None,2,None,3,None,4])},
    {'root': build_tree([0])},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        root = case['root']
        result = solve(root)
        out.append({
            'id': i,
            'input': {'arr': list(case.get('arr', []))} if 'arr' in case else {},
            'expected': json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
