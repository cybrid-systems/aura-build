import sys
import json

def solve(preorder: list, inorder: list):
    if not preorder:
        return []
    
    # Build index map for inorder positions
    inorder_index = {v: i for i, v in enumerate(inorder)}
    
    # Iterative construction to avoid recursion depth issues
    # Use a stack-based approach
    result = []
    
    # Stack entries: (node, pre_start, pre_end, in_start, in_end, state)
    # state: 0 = process left, 1 = process right, 2 = done
    
    root = preorder[0]
    # Use indices into preorder and inorder
    # We'll simulate recursion with a stack
    
    stack = []
    # Push root processing: preorder range [0, n), inorder range [0, n)
    stack.append((0, len(preorder), 0, len(inorder), False))
    
    while stack:
        pre_start, pre_end, in_start, in_end, visited = stack[-1]
        
        if pre_start >= pre_end:
            stack.pop()
            continue
        
        if not visited:
            # First visit: process this node
            root_val = preorder[pre_start]
            
            # Find root in inorder
            root_in_idx = inorder_index[root_val]
            
            # Left subtree size
            left_size = root_in_idx - in_start
            # Right subtree size
            right_size = in_end - root_in_idx - 1
            
            # Mark as visited, will process right subtree next then add to result
            stack[-1] = (pre_start, pre_end, in_start, in_end, True)
            
            # Push right subtree (process before adding this node to postorder)
            if right_size > 0:
                right_pre_start = pre_start + 1 + left_size
                right_pre_end = pre_end
                right_in_start = root_in_idx + 1
                right_in_end = in_end
                stack.append((right_pre_start, right_pre_end, right_in_start, right_in_end, False))
            
            # Push left subtree
            if left_size > 0:
                left_pre_start = pre_start + 1
                left_pre_end = pre_start + 1 + left_size
                left_in_start = in_start
                left_in_end = root_in_idx
                stack.append((left_pre_start, left_pre_end, left_in_start, left_in_end, False))
        else:
            # Visited: both subtrees processed, add this node
            stack.pop()
            result.append(preorder[pre_start])
    
    return result


CASES = [
    {
        "preorder": [4, 2, 1, 3, 6, 5, 7],
        "inorder": [1, 2, 3, 4, 5, 6, 7],
    },
    {
        "preorder": [],
        "inorder": [],
    },
    {
        "preorder": [1],
        "inorder": [1],
    },
    {
        "preorder": [1, 2, 3, 4, 5],
        "inorder": [5, 4, 3, 2, 1],
    },
    {
        "preorder": [1, 2, 3, 4, 5],
        "inorder": [1, 2, 3, 4, 5],
    },
    {
        "preorder": [3, 9, 20, 15, 7],
        "inorder": [9, 3, 15, 20, 7],
    },
    {
        "preorder": [5, 4, 3, 2, 1],
        "inorder": [1, 2, 3, 4, 5],
    },
    {
        "preorder": [1, 2, 3],
        "inorder": [2, 1, 3],
    },
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["preorder"], case["inorder"])
        results.append({
            "id": i,
            "input": {"preorder": case["preorder"], "inorder": case["inorder"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
