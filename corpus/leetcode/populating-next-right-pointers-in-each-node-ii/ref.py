import json
from collections import deque

class Node:
    def __init__(self, val=0, left=None, right=None, next=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next

def build_tree(values):
    if not values or values[0] == -1:
        return None
    root = Node(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        # left child
        if i < len(values) and values[i] != -1:
            node.left = Node(values[i])
            queue.append(node.left)
        i += 1
        # right child
        if i < len(values) and values[i] != -1:
            node.right = Node(values[i])
            queue.append(node.right)
        i += 1
    return root

def solve(root):
    if not root:
        return None
    
    # Use the next pointers of the previous level to traverse the current level
    leftmost = root
    
    while leftmost:
        # Iterate through the current level using next pointers
        # Build the next pointers for the next level
        dummy = Node(0)  # Dummy node to simplify linking
        prev = dummy
        
        current = leftmost
        while current:
            if current.left:
                prev.next = current.left
                prev = prev.next
            if current.right:
                prev.next = current.right
                prev = prev.next
            current = current.next
        
        # Move to the next level
        leftmost = dummy.next
    
    return root

def level_order_with_next(root):
    """Return the level-order encoding: val next val next ..."""
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        node = queue.popleft()
        result.append(node.val)
        result.append(0 if node.next is None else node.next.val)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    return result

# Test cases
CASES = [
    {"values": [1, 2, 3, 4, 5, -1, 7]},
    {"values": [1, 2, 3, 4, 5, 6, 7]},
    {"values": [1, -1, 2, -1, 3, -1, 4, -1, 5]},
    {"values": [1, 2, 3, -1, -1, -1, -1]},
    {"values": [1]},
    {"values": [-1]},
    {"values": [1, 2, -1, 3, -1, 4, -1]},
    {"values": [3, 9, 20, -1, -1, 15, 7]},
]

def run_case(case):
    values = case["values"][:]
    # Remove trailing -1 sentinel if present
    while values and values[-1] == -1:
        values.pop()
    
    # Build tree using the encoding (with -1 as null)
    full_values = case["values"]
    # Find actual length (stop at first -1 after valid nodes, but we need to handle 
    # the encoding properly - -1 in middle means null, trailing -1 terminates)
    # The format says sentinel -1 terminates the list
    # So we stop at the first -1 that comes after we've seen enough values
    # Actually re-reading: "A sentinel -1 terminates the list (any further values are ignored)"
    # This means we look for the terminating -1
    # For [1, 2, 3, 4, 5, -1, 7], the -1 is a null, not the sentinel
    # The sentinel is when we've consumed all nodes
    
    # Let's use the standard BFS build - children at 2*i+1, 2*i+2
    # We need to find where the tree actually ends
    
    # The simplest: find sentinel -1 (terminator). Looking at examples:
    # CASE0=1 2 3 4 5 -1 7 - the -1 here is the 5th child (position 5, index 5)
    #   which is right child of node at index 1 (val 2). So it's a null.
    #   Then 7 is at position 6, which is right child of node at index 2 (val 3).
    # So the tree has 7 nodes total.
    
    # Let's just build with proper BFS indices until we run out
    pass

def build_tree_v2(values):
    """Build tree from level-order encoding where -1 means null.
    The list is terminated by a sentinel -1."""
    if not values or values[0] == -1:
        return None
    
    # Find the actual end - we keep going until we have enough parent slots
    # The first -1 that, if we treat as null, still allows us to continue.
    # Actually, the simplest interpretation: stop when no more nodes can have children.
    # We need to figure out the length of the actual tree encoding.
    
    # From the problem: "A sentinel -1 terminates the list (any further values are ignored)"
    # So the actual encoding ends at the first -1 that could be a terminator.
    # Hmm, but in [1,2,3,4,5,-1,7], -1 is not a terminator.
    
    # Let me think: in BFS encoding, position i has children at 2i+1 and 2i+2.
    # The encoding includes nulls for missing nodes.
    # A sentinel -1 "terminates" - meaning we stop reading.
    
    # For [1,2,3,4,5,-1,7]:
    # pos 0: root=1
    # pos 1: left=2, pos 2: right=3
    # pos 3: left of 2 =4, pos 4: right of 2 =5
    # pos 5: left of 3 = -1 (null), pos 6: right of 3 = 7
    # So we need positions 0..6, that's 7 values.
    
    # The trick: the sentinel -1 could be ambiguous. Let's just check if there are valid
    # children slots remaining. We stop when:
    # - we've processed all values, or
    # - the next value is -1 AND it's not in a valid child slot (terminator)
    
    # Actually, the cleanest approach: just process values, when we hit -1, check if
    # it's a terminator. But how do we know?
    
    # Let's assume: the input list gives us all positions we need, and -1 in valid 
    # positions is null. We figure out length by: next index to fill.
    
    # Simpler: given that the problem provides "1 2 3 4 5 -1 7" as the full encoding,
    # we just use all values up to some point. Let's determine the length by finding
    # where the encoding ends.
    
    # Approach: stop when we've filled all parent nodes (so no more children would be valid)
    # Number of parents = (n+1)//2 where n is number of nodes
    # But n is unknown.
    
    # I'll use a heuristic: stop at the last value before trailing -1s that don't correspond
    # to any valid child position.
    
    # Actually, the cleanest: process values list. For each i from 0, place values[i] as 
    # child at 2*parent+1 or 2*parent+2. Stop when i >= len(values) or when we've processed
    # all parents.
    
    # Let's count: in encoding with n values (positions 0 to n-1), parents are at 
    # positions 0 to (n-1-1)//2. So if we have n values, parents go up to floor((n-1-1)/2).
    # For n=7: parents at 0,1,2. Children at 3,4,5,6. That's exactly 7 values, valid.
    # For n=6: [1,2,3,4,5,-1] - parents at 0,1,2. Children at 3,4,5. Value at 5 is -1 (left of 3).
    #   Right child of 3 would be at position 6, not provided. So tree has 6 nodes (5 real + 1 null).
    
    # OK so we just use all values up to len(values), and beyond that, treat as null.
    pass

def build_tree_final(values):
    """Final build logic: values is the full BFS encoding, -1 means null.
    We may need to extend with -1s to ensure all parent nodes have their children slots."""
    if not values or values[0] == -1:
        return None
    
    vals = list(values)
    # We need enough values so that every node has its two child slots
    # Find the actual length needed
    n = len(vals)
    # Count actual nodes (non -1)
    # We process positions 0, 1, 2, ... and at each non-null, it has children at 2i+1, 2i+2
    # So we need vals to be long enough that the last node's potential children are accounted for
    # The required length is: while there exists a node at position i where 2i+1 >= len(vals), extend
    
    # Let's just pad if needed (this handles the "sentinel terminates" case)
    changed = True
    while changed:
        changed = False
        for i in range(len(vals)):
            if vals[i] != -1:
                # This node needs slots 2i+1 and 2i+2
                if 2*i+2 >= len(vals):
                    vals.extend([-1] * (2*i+2 - len(vals) + 1))
                    changed = True
                    break
                if 2*i+1 >= len(vals):
                    vals.append(-1)
                    changed = True
                    break
    
    if not vals or vals[0] == -1:
        return None
    
    nodes = [None if v == -1 else Node(v) for v in vals]
    for i in range(len(vals)):
        if nodes[i] is not None:
            left_idx = 2*i + 1
            right_idx = 2*i + 2
            if left_idx < len(nodes):
                nodes[i].left = nodes[left_idx]
            if right_idx < len(nodes):
                nodes[i].right = nodes[right_idx]
    return nodes[0]

def run_case_final(case):
    values = case["values"]
    root = build_tree_final(values)
    root = solve(root)
    result = level_order_with_next(root)
    return result

if __name__ == '__main__':
    output = []
    for idx, case in enumerate(CASES):
        result = run_case_final(case)
        # Format as "CASE{i}=..."
        formatted = f"CASE{idx}=" + " ".join(str(x) for x in result)
        # But we need to output as a JSON array
        output.append({
            "id": idx,
            "input": {"values": case["values"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(output, separators=(',', ':'), ensure_ascii=False))
