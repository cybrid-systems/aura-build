def solve(m, n, board, word):
    if not word:
        return True
    
    # Convert empty cells ('.') - they won't match any character we care about,
    # but we still need to handle them in the grid.
    
    def dfs(i, j, idx):
        if idx == len(word):
            return True
        if i < 0 or i >= m or j < 0 or j >= n:
            return False
        if board[i][j] != word[idx]:
            return False
        if idx == len(word) - 1:
            return True
        
        # Mark visited
        temp = board[i][j]
        # Use a sentinel since board chars could be anything; we restore after
        # Actually board[i][j] already matched word[idx], mark with None
        board[i][j] = None
        
        found = (dfs(i + 1, j, idx + 1) or
                 dfs(i - 1, j, idx + 1) or
                 dfs(i, j + 1, idx + 1) or
                 dfs(i, j - 1, idx + 1))
        
        board[i][j] = temp
        return found
    
    for i in range(m):
        for j in range(n):
            if board[i][j] == word[0]:
                if dfs(i, j, 0):
                    return True
    return False


CASES = [
    {
        "m": 3,
        "n": 4,
        "board": [
            ['A', 'B', 'C', 'E'],
            ['S', 'F', 'C', 'S'],
            ['A', 'D', 'E', 'E']
        ],
        "word": "ABCCED"
    },
    {
        "m": 3,
        "n": 4,
        "board": [
            ['A', 'B', 'C', 'E'],
            ['S', 'F', 'C', 'S'],
            ['A', 'D', 'E', 'E']
        ],
        "word": "SEE"
    },
    {
        "m": 3,
        "n": 4,
        "board": [
            ['A', 'B', 'C', 'E'],
            ['S', 'F', 'C', 'S'],
            ['A', 'D', 'E', 'E']
        ],
        "word": "ABCB"
    },
    {
        "m": 1,
        "n": 1,
        "board": [['A']],
        "word": "A"
    },
    {
        "m": 1,
        "n": 1,
        "board": [['A']],
        "word": "AA"
    },
    {
        "m": 2,
        "n": 2,
        "board": [
            ['.', 'A'],
            ['B', 'C']
        ],
        "word": "AC"
    },
    {
        "m": 3,
        "n": 3,
        "board": [
            ['A', 'B', 'A'],
            ['B', 'A', 'B'],
            ['A', 'B', 'A']
        ],
        "word": "ABABABABA"
    },
    {
        "m": 2,
        "n": 2,
        "board": [
            ['A', 'B'],
            ['C', 'D']
        ],
        "word": ""
    },
]


if __name__ == '__main__':
    import json
    results = []
    for idx, case in enumerate(CASES):
        result = solve(case["m"], case["n"], [row[:] for row in case["board"]], case["word"])
        expected = "YES" if result else "NO"
        results.append({
            "id": idx,
            "input": {
                "m": case["m"],
                "n": case["n"],
                "board": case["board"],
                "word": case["word"]
            },
            "expected": expected
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
