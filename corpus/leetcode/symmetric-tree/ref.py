import sys, json, re

def parse_tree(s):
    s = s.strip()
    if s == 'null' or s == '#' or s == '':
        return None
    # Parse the S-expression format: (val left right)
    pos = [0]
    def parse():
        if pos[0] >= len(s):
            return None
        if s[pos[0]] == '#':
            pos[0] += 1
            return None
        if s[pos[0]] == ' ':
            pos[0] += 1
            return parse()
        if s[pos[0]] == '(':
            pos[0] += 1
            # Skip spaces
            while pos[0] < len(s) and s[pos[0]] == ' ':
                pos[0] += 1
            # Parse value
            start = pos[0]
            while pos[0] < len(s) and s[pos[0]] not in (' ', ')', '(', '#'):
                pos[0] += 1
            val_str = s[start:pos[0]]
            val = int(val_str) if val_str and val_str != 'null' else None
            left = parse()
            right = parse()
            if pos[0] < len(s) and s[pos[0]] == ')':
                pos[0] += 1
            return {'val': val, 'left': left, 'right': right}
        elif s[pos[0]] == 'n':
            # null
            if s[pos[0]:pos[0]+4] == 'null':
                pos[0] += 4
            return None
        else:
            # just a number or #
            start = pos[0]
            while pos[0] < len(s) and s[pos[0]] not in (' ', ')', '(', '#'):
                pos[0] += 1
            val_str = s[start:pos[0]]
            if val_str == '#' or val_str == 'null' or val_str == '':
                return None
            return {'val': int(val_str), 'left': None, 'right': None}
    return parse()

def is_symmetric(root):
    if root is None:
        return True
    def mirror(a, b):
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if a['val'] != b['val']:
            return False
        return mirror(a['left'], b['right']) and mirror(a['right'], b['left'])
    return mirror(root['left'], root['right'])

def parse_line(line):
    # Format: CASE0=(...)# or CASE0=value#
    # Find the '='
    idx = line.find('=')
    payload = line[idx+1:]
    # Remove trailing '#'
    if payload.endswith('#'):
        payload = payload[:-1]
    payload = payload.strip()
    if payload == 'null' or payload == '':
        return None
    return parse_tree(payload)

def solve(root):
    return is_symmetric(root)

CASES = [
    {"raw": "CASE0=(1 (2 (3 # #) (4 # #)) (2 (4 # #) (3 # #)))#"},  # symmetric
    {"raw": "CASE0=(1 (2 # #) (2 # #))#"},  # symmetric simple
    {"raw": "CASE0=(1 (2 # #) (3 # #))#"},  # not symmetric
    {"raw": "CASE0=(1)#"},  # single node -> symmetric
    {"raw": "CASE0=null#"},  # empty -> symmetric
    {"raw": "CASE0=(1 (2 (3 # #) #) (2 # (3 # #)))#"},  # symmetric
    {"raw": "CASE0=(1 (2 # (3 # #)) (2 (3 # #) #))#"},  # symmetric
    {"raw": "CASE0=(1 (2 (4 # #) (3 # #)) (2 (3 # #) (4 # #)))#"},  # asymmetric
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        line = case["raw"]
        root = parse_line(line)
        result = solve(root)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
