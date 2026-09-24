from typing import Optional, List


class Node:
    __slots__ = ("val", "next")

    def __init__(self, val: int = 0, nxt: Optional["Node"] = None):
        self.val = val
        self.next = nxt


def vec_to_list(v: List[int]) -> Optional[Node]:
    head = None
    tail = None
    for x in v:
        n = Node(x)
        if head is None:
            head = n
            tail = n
        else:
            tail.next = n
            tail = n
    return head


def list_to_vec(head: Optional[Node]) -> List[int]:
    out = []
    while head is not None:
        out.append(head.val)
        head = head.next
    return out


def push_back(head_ref: List[Optional[Node]], node: Node) -> None:
    if head_ref[0] is None:
        head_ref[0] = node
        head_ref[1] = node
    else:
        head_ref[1].next = node
        head_ref[1] = node


def solve(a: List[int], b: List[int]) -> List[int]:
    la = vec_to_list(a)
    lb = vec_to_list(b)

    # Build stacks of digits
    sa: List[int] = []
    sb: List[int] = []
    cur = la
    while cur is not None:
        sa.append(cur.val)
        cur = cur.next
    cur = lb
    while cur is not None:
        sb.append(cur.val)
        cur = cur.next

    carry = 0
    head_ref: List[Optional[Node]] = [None, None]  # [head, tail]
    i = len(sa) - 1
    j = len(sb) - 1
    while i >= 0 or j >= 0 or carry:
        da = sa[i] if i >= 0 else 0
        db = sb[j] if j >= 0 else 0
        s = da + db + carry
        carry = s // 10
        digit = s % 10
        n = Node(digit)
        # Prepend to result (since we computed units first → result is reversed)
        n.next = head_ref[0]
        head_ref[0] = n
        if head_ref[1] is None:
            head_ref[1] = n
        i -= 1
        j -= 1

    return list_to_vec(head_ref[0])


CASES = [
    {"a": [7, 2, 4], "b": [5, 6]},
    {"a": [2, 4, 3], "b": [5, 6, 4]},
    {"a": [0], "b": [0]},
    {"a": [9, 9], "b": [1]},
    {"a": [1], "b": [9, 9, 9]},
    {"a": [9, 9, 9, 9, 9, 9, 9], "b": [9, 9, 9, 9]},
    {"a": [5, 0, 0], "b": [5, 0, 0]},
    {"a": [1, 2, 3, 4, 5], "b": [6, 7, 8]},
]


if __name__ == "__main__":
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
