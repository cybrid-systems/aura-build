import json, os

def calculate(s):
    """Evaluate expression with +, -, *, / respecting precedence, trunc div toward zero."""
    s = s.replace(' ', '')
    if not s:
        return 0
    stack = []
    num = 0
    op = '+'  # pending operator for next number
    for i, ch in enumerate(s + '+'):  # trailing op forces flush of last num
        if ch.isdigit():
            num = num * 10 + ord(ch) - 48
        if not ch.isdigit() and ch != '.' or i == len(s) - 1:
            # ch is an operator here (or end). 'op' holds operator BEFORE current num.
            if op == '+':
                stack.append(num)
            elif op == '-':
                stack.append(-num)
            elif op == '*':
                stack.append(stack.pop() * num)
            elif op == '/':
                # Truncation toward zero: both operands non-negative here.
                a = stack.pop()
                stack.append(int(a / num) if num != 0 else 0)
            op = ch
            num = 0
    return sum(stack)

def solve(s):
    return calculate(s)

CASES = [
    {"s": "3+2*2"},
    {"s": " 3/2 "},
    {"s": " 3+5 / 2 "},
    {"s": "0"},
    {"s": "1-1-1"},
    {"s": "14/3*2"},
    {"s": "1000000/6/2"},
    {"s": "1*2*3*4*5"},
    {"s": " 6/4 "},
    {"s": "10-6/2+3*2"},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["s"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
