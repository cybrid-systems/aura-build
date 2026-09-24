import json

def solve(s, t):
    result = 0
    for c in s:
        result ^= ord(c)
    for c in t:
        result ^= ord(c)
    return chr(result)

CASES = [
    {"s": "abcde", "t": "abecdfe"},
    {"s": "", "t": "a"},
    {"s": "a", "t": "aa"},
    {"s": "abcd", "t": "abcde"},
    {"s": "hello", "t": "helollo"},
    {"s": "thequickbrownfoxjumpsoverthelazydog", "t": "thequickbrownfoxjumpsoverthelazydogx"},
    {"s": "abcdefghijklmnopqrstuvwxyz", "t": "abcdefghijklmnopqrstuvwxyz!"},
    {"s": "z", "t": "zz"},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(s=case["s"], t=case["t"])
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
