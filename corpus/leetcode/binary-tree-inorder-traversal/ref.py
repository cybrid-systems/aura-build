import json
from typing import Optional, List, Any

def solve(aura: dict) -> List[int]:
    tree = aura.get("tree") if isinstance(aura, dict) else None
    
    def inorder(node: Optional[dict]) -> List[int]:
        if node is None:
            return []
        result = []
        # Inorder: Left -> Node -> Right
        result.extend(inorder(node.get("left")))
        value = node.get("value")
        if value is not None:
            result.append(value)
        result.extend(inorder(node.get("right")))
        return result
    
    return inorder(tree)

CASES = [
    {"aura": {"tree": {"value": 1, "left": {"value": 2, "left": None, "right": None}, "right": {"value": 3, "left": None, "right": None}}}},
    {"aura": {"tree": {"value": None, "left": None, "right": None}}},
    {"aura": {"tree": {"value": 1, "left": None, "right": None}}},
    {"aura": {"tree": {"value": 1, "left": {"value": 2, "left": {"value": 4, "left": None, "right": None}, "right": {"value": 5, "left": None, "right": None}}, "right": {"value": 3, "left": None, "right": {"value": 6, "left": None, "right": None}}}}},
    {"aura": {"tree": None}},
    {"aura": {"tree": {"value": -5, "left": {"value": -10, "left": None, "right": None}, "right": {"value": 0, "left": None, "right": None}}}},
    {"aura": {"tree": {"value": 1, "left": {"value": 2, "left": {"value": 4, "left": None, "right": None}, "right": None}, "right": {"value": 3, "left": None, "right": None}}}},
    {"aura": {"tree": {"value": 5, "left": {"value": 3, "left": {"value": 1, "left": None, "right": None}, "right": {"value": 4, "left": None, "right": None}}, "right": {"value": 8, "left": {"value": 7, "left": None, "right": None}, "right": {"value": 9, "left": None, "right": None}}}}},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
