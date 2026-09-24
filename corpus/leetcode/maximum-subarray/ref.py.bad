import sys
import json

def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    current = max_sum = nums[0]
    for x in nums[1:]:
        current = max(x, current + x)
        if current > max_sum:
            max_sum = current
    return max_sum


CASES = [
    {"id": 0, "input": {"nums": [1, -2, 3, -1, 2, -1, 5, -4]}},
    {"id": 1, "input": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}},
    {"id": 2, "input": {"nums": [-1, -2, -3, -4]}},
    {"id": 3, "input": {"nums": [5]}},
    {"id": 4, "input": {"nums": [1, 2, 3, 4, 5]}},
    {"id": 5, "input": {"nums": [-1, 2, -1, 3, -2, 4]}},
    {"id": 6, "input": {"nums": [0, -1, 0, -1, 0]}},
    {"id": 7, "input": {"nums": [1, -1, 1, -1, 1, -1, 1]}},
]


def parse_input(raw: str):
    lines = raw.splitlines()
    cases = []
    current = None
    for line in lines:
        if line.startswith("CASE") and "=" in line:
            if current is not None:
                cases.append(current)
            case_id = line.split("=", 1)[0].replace("CASE", "").strip()
            current = {"id": int(case_id), "nums": []}
        elif line.strip() and current is not None:
            current["nums"] = [int(x) for x in line.split()]
    if current is not None:
        cases.append(current)
    return cases


if __name__ == "__main__":
    # Run solve on each case (both via the harness input format and direct CASES dicts)
    # Build output JSON of all cases including expected computed values
    out_cases = []
    for case in CASES:
        nums = case["input"]["nums"]
        result = solve(nums)
        out_cases.append({
            "id": case["id"],
            "input": {"nums": nums},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })

    # Also demonstrate parsing the harness-style input (informational)
    raw = "CASE0=\n1 -2 3 -1 2 -1 5 -4\n"
    parsed = parse_input(raw)
    # assert parsed matches first case logic (sanity)
    if parsed:
        parsed_result = solve(parsed[0]["nums"])
        # ensure consistency
        assert parsed_result == out_cases[0]["expected"]

    print(json.dumps(out_cases, separators=(',', ':'), ensure_ascii=False))
