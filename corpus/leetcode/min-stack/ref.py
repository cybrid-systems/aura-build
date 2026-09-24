import json
from typing import List, Tuple, Union

def solve(ops: List[Tuple[Union[int, str], ...]]) -> List[int]:
    main_stack = []
    min_stack = []
    result = []
    for op in ops:
        t = op[0]
        if t == 1 or t == '1':
            x = op[1]
            main_stack.append(x)
            if not min_stack or x <= min_stack[-1]:
                min_stack.append(x)
        elif t == 2 or t == '2':
            if main_stack:
                v = main_stack.pop()
                if min_stack and v == min_stack[-1]:
                    min_stack.pop()
        elif t == 3 or t == '3':
            if min_stack:
                result.append(min_stack[-1])
    return result

CASES = [
    {"ops": [(1,5),(1,2),(1,8),(3,),(2,),(2,),(1,3),(3,),(2,),(2,)]},
    {"ops": [(1,1),(3,),(2,)]},
    {"ops": [(1,-5),(1,0),(1,7),(3,),(3,),(2,),(3,),(2,),(2,)]},
    {"ops": [(1,10),(3,),(1,5),(3,),(2,),(3,),(2,)]},
    {"ops": [(1,3),(1,3),(3,),(2,),(2,)]},
    {"ops": [(1,2),(1,1),(3,),(2,),(3,)]},
    {"ops": [(1,-100),(1,100),(3,),(1,-50),(3,),(2,),(3,)]},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        res = solve(c["ops"])
        out.append({"id": i, "input": c, "expected": json.dumps(res, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
