def solve(n: int, target: int, position: list[int], speed: list[int]) -> int:
    # Pair cars with their data and sort by position descending
    cars = sorted(zip(position, speed), key=lambda x: -x[0])
    
    fleets = 0
    max_time = 0.0
    
    for pos, spd in cars:
        time = (target - pos) / spd
        if time > max_time:
            # New fleet leader (strictly greater time)
            fleets += 1
            max_time = time
        # else: this car catches up to / arrives with a fleet ahead
    
    return fleets


CASES = [
    # Case 0: Example from problem - 3 fleets
    {"n": 3, "target": 12, "position": [10, 8, 0], "speed": [2, 4, 1]},
    # Case 1: Single car
    {"n": 1, "target": 10, "position": [0], "speed": [1]},
    # Case 2: Two cars, same fleet (faster behind catches slower)
    {"n": 2, "target": 12, "position": [4, 0], "speed": [1, 4]},
    # Case 3: Two cars, separate fleets (slower behind)
    {"n": 2, "target": 12, "position": [10, 0], "speed": [2, 1]},
    # Case 4: Multiple cars all forming one fleet
    {"n": 4, "target": 25, "position": [6, 4, 2, 0], "speed": [2, 1, 1, 1]},
    # Case 5: Each car arrives at different time -> n fleets
    {"n": 3, "target": 100, "position": [10, 20, 30], "speed": [1, 1, 1]},
    # Case 6: Equal arrival times (strictly-less rule -> 2 fleets)
    {"n": 3, "target": 12, "position": [8, 6, 0], "speed": [2, 1, 1]},
    # Case 7: Classic LeetCode example (target=12, pos=[10,8,0,5,3], spd=[2,4,1,1,2]) -> 3
    {"n": 5, "target": 12, "position": [10, 8, 0, 5, 3], "speed": [2, 4, 1, 1, 2]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["n"], case["target"], case["position"], case["speed"])
        results.append({"id": i, "input": case, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
