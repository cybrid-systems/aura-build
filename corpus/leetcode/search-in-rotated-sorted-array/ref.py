import sys
import json

def solve(nums: list, target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        # Left half is sorted
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            # Right half is sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


CASES = [
    {"id": 0, "nums": [4, 5, 6, 7, 0, 1, 2], "target": 0},
    {"id": 1, "nums": [4, 5, 6, 7, 0, 1, 2], "target": 3},
    {"id": 2, "nums": [1], "target": 0},
    {"id": 3, "nums": [1], "target": 1},
    {"id": 4, "nums": [0, 1, 2, 4, 5, 6, 7], "target": 4},
    {"id": 5, "nums": [4, 5, 6, 7, 0, 1, 2], "target": 5},
    {"id": 6, "nums": [3, 1], "target": 1},
    {"id": 7, "nums": [5, 1, 3], "target": 3},
]


def _parse_input():
    data = sys.stdin.read()
    marker = "CASE0="
    idx = data.find(marker)
    if idx == -1:
        # try alternate "Case" markers
        for prefix in ["Case0=", "case0="]:
            idx = data.find(prefix)
            if idx != -1:
                marker = prefix
                break
    if idx == -1:
        return None
    payload = data[idx + len(marker):].strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        # try to find first {...} block
        start = payload.find("{")
        end = payload.rfind("}")
        if start != -1 and end != -1:
            return json.loads(payload[start:end + 1])
        return None


def main():
    case = _parse_input()
    if case is not None:
        nums = case["nums"]
        target = case["target"]
        result = solve(nums, target)
        print(result)
        return

    # Fallback: run through CASES for verification/logging
    out = []
    for c in CASES:
        result = solve(c["nums"], c["target"])
        out.append({
            "id": c["id"],
            "input": {"nums": c["nums"], "target": c["target"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
