import json


def solve(people):
    # Sort by height descending; for equal heights, smaller k first so that
    # when we insert at index k, the previously-inserted equal-height people
    # already occupy positions consistent with their own k values.
    sorted_people = sorted(people, key=lambda p: (-p[0], p[1]))
    result = []
    for person in sorted_people:
        result.insert(person[1], person)
    return result


CASES = [
    {"people": [[7, 0], [4, 4], [7, 1], [5, 0], [6, 1], [5, 2]]},
    {"people": []},
    {"people": [[1, 0]]},
    {"people": [[5, 0], [4, 0], [3, 0], [2, 0], [1, 0]]},
    {"people": [[6, 0], [5, 1], [4, 2], [3, 3], [2, 4], [1, 5]]},
    {"people": [[10, 0], [10, 1], [10, 2], [10, 3]]},
    {"people": [[100, 0], [90, 1], [80, 2], [70, 3], [60, 4]]},
    {"people": [[5, 0], [5, 1], [5, 2], [4, 0], [4, 1], [4, 2], [3, 0]]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["people"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
