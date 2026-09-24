import json
from typing import List


class TrieNode:
    __slots__ = ("children", "word")

    def __init__(self):
        self.children = {}
        self.word = None


def solve(board: List[List[str]], words: List[str]) -> List[str]:
    if not board or not board[0] or not words:
        return []

    root = TrieNode()
    for w in words:
        node = root
        for ch in w:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.word = w

    rows, cols = len(board), len(board[0])
    found = []

    def dfs(r: int, c: int, node: TrieNode) -> None:
        ch = board[r][c]
        if ch not in node.children:
            return
        nxt = node.children[ch]
        if nxt.word is not None:
            found.append(nxt.word)
            nxt.word = None  # avoid duplicates
        # Prune: if this node has no children, remove it from parent
        if not nxt.children:
            del node.children[ch]
            return

        # Mark visited
        board[r][c] = "#"
        # Neighbors
        nr, nc = r - 1, c
        if nr >= 0:
            dfs(nr, nc, nxt)
        nr, nc = r + 1, c
        if nr < rows:
            dfs(nr, nc, nxt)
        nr, nc = r, c - 1
        if nc >= 0:
            dfs(nr, nc, nxt)
        nr, nc = r, c + 1
        if nc < cols:
            dfs(nr, nc, nxt)
        # Restore
        board[r][c] = ch

    for i in range(rows):
        for j in range(cols):
            if board[i][j] in root.children:
                dfs(i, j, root)

    return found


CASES = [
    {
        "id": 0,
        "input": {
            "board": [["o","a","a","n"],["e","t","a","e"],["i","h","k","r"],["i","f","l","v"]],
            "words": ["oath","pea","eat","rain"],
        },
    },
    {
        "id": 1,
        "input": {
            "board": [["a","b"],["c","d"]],
            "words": ["ab","cb","abcd","abc","bd","acbd","abcbd","abcbd"],
        },
    },
    {
        "id": 2,
        "input": {
            "board": [["a"]],
            "words": ["a","b","aa"],
        },
    },
    {
        "id": 3,
        "input": {
            "board": [["a","a","a"],["a","a","a"],["a","a","a"]],
            "words": ["a","aa","aaa","aaaa","b"],
        },
    },
    {
        "id": 4,
        "input": {
            "board": [["o","a","a","n"],["e","t","a","e"],["i","h","k","r"],["i","f","l","v"]],
            "words": ["oath","pea","eat","rain","oath","oat","oatho","oatf"],
        },
    },
    {
        "id": 5,
        "input": {
            "board": [["a","b","c"],["d","e","f"],["g","h","i"]],
            "words": ["abc","aei","cfi","a","z","abfie","abfiec"],
        },
    },
]


if __name__ == "__main__":
    out = []
    for case in CASES:
        # Deep copy board so each case starts clean
        inp = case["input"]
        board_copy = [row[:] for row in inp["board"]]
        result = solve(board_copy, list(inp["words"]))
        # Sort result for canonical comparison
        result_sorted = sorted(result)
        out.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(result_sorted, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
