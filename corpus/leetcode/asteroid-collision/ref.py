def solve(asteroids):
    stack = []
    for a in asteroids:
        # Process current asteroid against stack top
        alive = True
        while alive and stack and stack[-1] > 0 and a < 0:
            top = stack[-1]
            # Collision: top moves right, a moves left
            if top < -a:
                # Top destroyed, check next
                stack.pop()
            elif top == -a:
                # Both destroyed
                stack.pop()
                alive = False
            else:
                # a destroyed, top survives
                alive = False
        if alive:
            stack.append(a)
    return stack


CASES = [
    {"args": [5, 10, -5]},
    {"args": [8, -8]},
    {"args": [10, 2, -5]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["args"])
        canonical = "[" + " ".join(str(x) for x in out) + "]"
        results.append({"id": i, "input": {"args": case["args"]}, "expected": canonical})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
