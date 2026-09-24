import sys
import json

def solve(root):
    if root is None:
        return []
    sums = []
    counts = []
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if depth >= len(sums):
            sums.append(0.0)
            counts.append(0)
        sums[depth] += node['val']
        counts[depth] += 1
        if node.get('right') is not None:
            stack.append((node['right'], depth + 1))
        if node.get('left') is not None:
            stack.append((node['left'], depth + 1))
    return [s / c for s, c in zip(sums, counts)]

def parse_level_order(tokens):
    if not tokens or tokens[0] == 'null':
        return None
    root = {'val': int(tokens[0]), 'left': None, 'right': None}
    queue = [root]
    i = 1
    n = len(tokens)
    while queue and i < n:
        node = queue.pop(0)
        if i < n:
            if tokens[i] == 'null':
                node['left'] = None
            else:
                left = {'val': int(tokens[i]), 'left': None, 'right': None}
                node['left'] = left
                queue.append(left)
            i += 1
        if i < n:
            if tokens[i] == 'null':
                node['right'] = None
            else:
                right = {'val': int(tokens[i]), 'left': None, 'right': None}
                node['right'] = right
                queue.append(right)
            i += 1
    return root

def main():
    data = sys.stdin.read().strip().splitlines()
    cases = []
    for line in data:
        line = line.strip()
        if not line or not line.startswith('CASE0='):
            continue
        tokens = line[len('CASE0='):].split()
        root = parse_level_order(tokens)
        cases.append(root)
    results = []
    for root in cases:
        avgs = solve(root)
        results.append({
            'id': 0,
            'input': 'CASE0=' + (' '.join(sys.stdin.read().strip().splitlines()[0].split()[1:]) if False else ''),
            'expected': ' '.join(f'{a:.5f}' for a in avgs)
        })
    # Reconstruct expected from actual solve; we need original input tokens per case.
    out_lines = []
    idx = 0
    for line in data:
        line = line.strip()
        if not line or not line.startswith('CASE0='):
            continue
        tokens = line[len('CASE0='):].split()
        root = parse_level_order(tokens)
        avgs = solve(root)
        out_lines.append(' '.join(f'{a:.5f}' for a in avgs))
        idx += 1
    print('\n'.join(out_lines))

CASES = [
    {'tokens': ['3', '9', '20', 'null', 'null', '15', '7']},
    {'tokens': ['1', 'null', '2']},
    {'tokens': ['-1', 'null', '2', 'null', '3', 'null', '4', 'null', '5']},
    {'tokens': ['0', '0', '0', '0', '0']},
    {'tokens': ['5']},
    {'tokens': ['10', '5', '15', '3', '7', 'null', '20']},
]

if __name__ == '__main__':
    case_results = []
    for i, case in enumerate(CASES):
        root = parse_level_order(case['tokens'])
        result = solve(root)
        result_str = ' '.join(f'{a:.5f}' for a in result)
        case_results.append({
            'id': i,
            'input': {'tokens': case['tokens']},
            'expected': result_str
        })
    print(json.dumps(case_results, separators=(',', ':'), ensure_ascii=False))
