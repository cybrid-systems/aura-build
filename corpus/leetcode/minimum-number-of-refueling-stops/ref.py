import json
import heapq


def solve(target, start_fuel, stations):
    n = len(stations)
    if start_fuel >= target:
        return 0
    # If no stations and can't reach target
    if n == 0:
        return -1
    # If can't reach first station
    if stations[0][0] > start_fuel:
        return -1

    # Max-heap (use negative values for min-heap)
    max_heap = []
    prev = 0
    fuel = start_fuel
    stops = 0
    i = 0

    while fuel < target:
        # Add all reachable stations to heap
        while i < n and stations[i][0] - prev <= fuel:
            heapq.heappush(max_heap, -stations[i][1])
            i += 1

        if not max_heap:
            return -1

        # Refuel at station with max fuel
        fuel += -heapq.heappop(max_heap)
        stops += 1
        # Update prev to the position of the station we just refueled
        # We need to know which station was popped
        # Actually, prev should track the position from which we are now calculating reach
        # This is tricky because heap doesn't tell us the position
        # We need a different approach: use prev as the position of the last refueled station
        # But we don't know that from the heap alone

    return stops


# Better approach: iterate through stations and use heap
def solve(target, start_fuel, stations):
    max_heap = []
    fuel = start_fuel
    prev_pos = 0
    stops = 0

    for pos, fuel_amount in stations:
        # Distance from prev_pos to current station
        dist = pos - prev_pos
        # Need fuel to reach this station
        while fuel < dist:
            if not max_heap:
                return -1
            fuel += -heapq.heappop(max_heap)
            stops += 1
        fuel -= dist
        heapq.heappush(max_heap, -fuel_amount)
        prev_pos = pos

    # After all stations, try to reach target
    dist = target - prev_pos
    while fuel < dist:
        if not max_heap:
            return -1
        fuel += -heapq.heappop(max_heap)
        stops += 1
    fuel -= dist

    return stops


CASES = [
    # Case 0: example from problem
    {"target": 100, "start_fuel": 10, "stations": [[10, 20], [20, 30], [30, 40], [60, 50]]},
    # Case 1: can reach target without any stops
    {"target": 100, "start_fuel": 200, "stations": [[10, 20], [20, 30]]},
    # Case 2: no stations, can't reach target
    {"target": 100, "start_fuel": 10, "stations": []},
    # Case 3: no stations, can reach target
    {"target": 50, "start_fuel": 50, "stations": []},
    # Case 4: can't reach first station
    {"target": 100, "start_fuel": 5, "stations": [[10, 20], [20, 30]]},
    # Case 5: classic example - answer is 2
    {"target": 1, "start_fuel": 1, "stations": []},
    # Case 6: need to stop at all stations strategically
    {"target": 100, "start_fuel": 25, "stations": [[25, 25], [50, 25], [75, 25]]},
    # Case 7: impossible - heap becomes empty
    {"target": 1000, "start_fuel": 100, "stations": [[200, 100], [400, 100], [600, 100], [800, 100]]},
]


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["target"], case["start_fuel"], case["stations"])
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
