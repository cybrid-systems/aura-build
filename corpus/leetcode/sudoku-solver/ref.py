def solve(board_lines):
    # board_lines: list of 9 strings of length 9, with '.' for empty
    board = [list(row) for row in board_lines]
    rows = [0]*9
    cols = [0]*9
    boxes = [0]*9
    empties = []
    for i in range(9):
        for j in range(9):
            c = board[i][j]
            if c == '.':
                empties.append((i,j))
            else:
                d = int(c) - 1
                bit = 1 << d
                rows[i] |= bit
                cols[j] |= bit
                boxes[(i//3)*3 + j//3] |= bit
    # backtrack
    def backtrack(k):
        if k == len(empties):
            return True
        # choose empty with minimum candidates (MRV)
        best_idx = -1
        best_count = 10
        best_mask = 0
        for idx in range(k, len(empties)):
            i,j = empties[idx]
            b = (i//3)*3 + j//3
            mask = ~(rows[i] | cols[j] | boxes[b]) & 0x1FF
            cnt = bin(mask).count('1')
            if cnt < best_count:
                best_count = cnt
                best_mask = mask
                best_idx = idx
                if cnt == 1:
                    break
                if cnt == 0:
                    return False
        # swap best to position k
        empties[k], empties[best_idx] = empties[best_idx], empties[k]
        i,j = empties[k]
        b = (i//3)*3 + j//3
        mask = best_mask
        m = mask
        while m:
            d_bit = m & -m
            d = (d_bit.bit_length() - 1)
            board[i][j] = str(d+1)
            rows[i] |= d_bit
            cols[j] |= d_bit
            boxes[b] |= d_bit
            if backtrack(k+1):
                return True
            rows[i] ^= d_bit
            cols[j] ^= d_bit
            boxes[b] ^= d_bit
            m ^= d_bit
        board[i][j] = '.'
        empties[k], empties[best_idx] = empties[best_idx], empties[k]
        return False
    backtrack(0)
    return '\n'.join(''.join(row) for row in board) + '\n'

CASES = [
    {"id":0, "board":[
        "53..7....",
        "6..195...",
        ".98....6.",
        "8...6...3",
        "4..8.3..1",
        "7...2...6",
        ".6....28.",
        "...419..5",
        "....8..79"
    ]},
    {"id":1, "board":[
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        "........."
    ]},
    {"id":2, "board":[
        "123456789",
        "456789123",
        "789123456",
        "234567891",
        "567891234",
        "891234567",
        "345678912",
        "678912345",
        "912345678"
    ]},
    {"id":3, "board":[
        "1........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        "........."
    ]},
    {"id":4, "board":[
        "..2...3..",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        "........."
    ]},
    {"id":5, "board":[
        ".1.2.3.4.",
        "5.6.7.8.9",
        ".1.2.3.4.",
        "5.6.7.8.9",
        ".1.2.3.4.",
        "5.6.7.8.9",
        ".1.2.3.4.",
        "5.6.7.8.9",
        ".1.2.3.4."
    ]},
    {"id":6, "board":[
        "9........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        ".........",
        "........."
    ]},
]

if __name__ == '__main__':
    import json
    out = []
    for case in CASES:
        result = solve(case["board"])
        # the problem's output format includes solved board plus '#'; we return
        # the 9 lines here, and the test harness can append '#'. To keep the
        # JSON self-contained, we include the trailing '#' line.
        out.append({
            "id": case["id"],
            "input": {"board": case["board"]},
            "expected": result.strip() + "\n#"
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
