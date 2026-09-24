def solve(head, n):
    """Remove nth node from end of linked list using two pointers."""
    if not head:
        return []
    
    # Create a dummy node to handle edge case of removing head
    dummy = ListNode(0)
    dummy.next = ListNode(head[0])
    current = dummy.next
    for i in range(1, len(head)):
        current.next = ListNode(head[i])
        current = current.next
    
    slow = dummy
    fast = dummy
    
    # Advance fast pointer n steps ahead
    for _ in range(n):
        fast = fast.next
    
    # Move both until fast reaches the end
    while fast.next is not None:
        slow = slow.next
        fast = fast.next
    
    # Remove the node after slow
    slow.next = slow.next.next
    
    # Convert back to list
    result = []
    node = dummy.next
    while node is not None:
        result.append(node.val)
        node = node.next
    
    return result


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def parse_case(line):
    """Parse 'head=1,2,3,4,5;n=2' into (head_list, n)."""
    parts = line.split(';')
    head_part = parts[0].split('=')[1]
    n_part = parts[1].split('=')[1]
    
    if head_part:
        head = [int(x) for x in head_part.split(',')]
    else:
        head = []
    
    n = int(n_part)
    return head, n


CASES = [
    {"head": [1, 2, 3, 4, 5], "n": 2},
    {"head": [1], "n": 1},
    {"head": [1, 2], "n": 1},
    {"head": [1, 2], "n": 2},
    {"head": [1, 2, 3], "n": 3},
    {"head": [1, 2, 3, 4, 5], "n": 5},
    {"head": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100], "n": 4},
    {"head": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "n": 1},
]


if __name__ == '__main__':
    import sys
    import json
    
    results = []
    for i, case in enumerate(CASES):
        head = case["head"]
        n = case["n"]
        result = solve(head, n)
        expected_str = ",".join(str(x) for x in result)
        results.append({
            "id": i,
            "input": {"head": head, "n": n},
            "expected": expected_str
        })
    
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
