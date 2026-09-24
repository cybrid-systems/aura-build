import json

def solve(root):
    """Check if a binary tree is height-balanced.
    
    Node format: {:val v :left l :right r} or None
    """
    def check(node):
        # Returns (is_balanced, height)
        if node is None:
            return True, 0
        # Recursively check left and right subtrees
        left_bal, left_h = check(node.get('left'))
        if not left_bal:
            return False, 0  # height doesn't matter
        right_bal, right_h = check(node.get('right'))
        if not right_bal:
            return False, 0
        # Check balance at this node
        if abs(left_h - right_h) > 1:
            return False, 0
        return True, max(left_h, right_h) + 1
    
    is_balanced, _ = check(root)
    return is_balanced


# Test cases - all match the problem's on-disk format style
# Each case describes the tree structure and expects a boolean answer

CASES = [
    # Case 0: Empty tree - balanced
    {
        "root": None
    },
    # Case 1: Single node - balanced
    {
        "root": {"val": 1, "left": None, "right": None}
    },
    # Case 2: Perfectly balanced tree of 3 nodes
    {
        "root": {
            "val": 1,
            "left": {"val": 2, "left": None, "right": None},
            "right": {"val": 3, "left": None, "right": None}
        }
    },
    # Case 3: Linked-list style (right-skewed) - unbalanced
    {
        "root": {
            "val": 1,
            "left": None,
            "right": {
                "val": 2,
                "left": None,
                "right": {
                    "val": 3,
                    "left": None,
                    "right": None
                }
            }
        }
    },
    # Case 4: Root balanced but deeper node unbalanced
    #       1
    #      / \
    #     2   3
    #    /
    #   4
    #     \
    #      5
    {
        "root": {
            "val": 1,
            "left": {
                "val": 2,
                "left": {
                    "val": 4,
                    "left": None,
                    "right": {"val": 5, "left": None, "right": None}
                },
                "right": None
            },
            "right": {"val": 3, "left": None, "right": None}
        }
    },
    # Case 5: Larger balanced tree
    {
        "root": {
            "val": 1,
            "left": {
                "val": 2,
                "left": {"val": 4, "left": None, "right": None},
                "right": {"val": 5, "left": None, "right": None}
            },
            "right": {
                "val": 3,
                "left": {"val": 6, "left": None, "right": None},
                "right": {"val": 7, "left": None, "right": None}
            }
        }
    },
    # Case 6: Left-skewed chain - unbalanced
    {
        "root": {
            "val": 1,
            "left": {
                "val": 2,
                "left": {
                    "val": 3,
                    "left": {
                        "val": 4,
                        "left": None,
                        "right": None
                    },
                    "right": None
                },
                "right": None
            },
            "right": None
        }
    },
    # Case 7: Balanced at root but unbalanced deep
    #         1
    #        / \
    #       2   2
    #      /     \
    #     3       3
    #    /         \
    #   4           4
    {
        "root": {
            "val": 1,
            "left": {
                "val": 2,
                "left": {
                    "val": 3,
                    "left": {"val": 4, "left": None, "right": None},
                    "right": None
                },
                "right": None
            },
            "right": {
                "val": 2,
                "left": None,
                "right": {
                    "val": 3,
                    "left": None,
                    "right": {"val": 4, "left": None, "right": None}
                }
            }
        }
    },
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        input_data = {"root": case["root"]}
        result = solve(case["root"])
        results.append({
            "id": i,
            "input": input_data,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
