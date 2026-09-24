import sys
import json


def solve(gas, cost):
    """
    Returns the unique starting index such that a circular tour is possible,
    or -1 if no such index exists.

    Classic greedy solution:
      - If sum(gas) < sum(cost), return -1.
      - Otherwise, scan once keeping a running tank level; the candidate start
        is the index right after the point where the tank would have dipped
        lowest (equivalently, the index where the running surplus against
        current start is minimized).
    """
    n = len(gas)
    if n == 0:
        return -1

    total_gas = 0
    total_cost = 0
    tank = 0
    start = 0
    for i in range(n):
        total_gas += gas[i]
        total_cost += cost[i]
        tank += gas[i] - cost[i]
        if tank < 0:
            # cannot start here nor at any prior station;
            # try starting at the next station.
            start = i + 1
            tank = 0

    if total_gas < total_cost:
        return -1
    # start could be n if all tanks were nonnegative; wrap is impossible,
    # but if total_gas >= total_cost, this won't happen.
    return start % n


def parse_input(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    data = {}
    for ln in lines:
        if '=' not in ln:
            continue
        k, v = ln.split('=', 1)
        data[k.strip()] = v.strip()
    n = int(data['N'])
    gas = list(map(int, data['GAS'].split()))
    cost = list(map(int, data['COST'].split()))
    return n, gas, cost


CASES = [
    # Classic example from the statement's sample idea
    {'gas': [1, 2, 3], 'cost': [2, 1, 0]},
    # No valid start (sum gas < sum cost)
    {'gas': [1, 1, 1], 'cost': [2, 2, 2]},
    # Single station, feasible only if gas >= cost
    {'gas': [5], 'cost': [5]},
    # Single station, infeasible
    {'gas': [3], 'cost': [5]},
    # All zeros
    {'gas': [0, 0, 0], 'cost': [0, 0, 0]},
    # Wrap-around, start at last station
    {'gas': [2, 3, 4], 'cost': [3, 4, 3]},
    # Larger random-ish scenario, start somewhere in the middle
    {'gas': [0, 0, 5, 0, 1, 2, 3, 0, 0, 1], 'cost': [1, 2, 0, 3, 0, 0, 1, 5, 0, 1]},
    # Case where sum(gas) == sum(cost), feasible
    {'gas': [2, 2, 2, 2], 'cost': [1, 3, 1, 3]},
]


def main():
    text = sys.stdin.read()
    results = []
    for case in CASES:
        res = solve(case['gas'], case['cost'])
        results.append({
            'id': len(results),
            'input': {
                'gas': case['gas'],
                'cost': case['cost'],
            },
            'expected': json.dumps(res, separators=(',', ':'), ensure_ascii=False),
        })

    if text.strip():
        n, gas, cost = parse_input(text)
        results.append({
            'id': len(results),
            'input': {'gas': gas, 'cost': cost},
            'expected': json.dumps(solve(gas, cost), separators=(',', ':'), ensure_ascii=False),
        })

    sys.stdout.write(json.dumps(results, separators=(',', ':'), ensure_ascii=False))


if __name__ == '__main__':
    main()
