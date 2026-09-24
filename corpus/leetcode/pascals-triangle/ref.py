import os
import json


def generate_pascals_triangle(num_rows):
    """Generate the first num_rows of Pascal's triangle."""
    rows = []
    for i in range(num_rows):
        if i == 0:
            rows.append([1])
        else:
            prev = rows[-1]
            new_row = [1]
            for j in range(len(prev) - 1):
                new_row.append(prev[j] + prev[j + 1])
            new_row.append(1)
            rows.append(new_row)
    return rows


def solve(num_rows):
    rows = generate_pascals_triangle(num_rows)
    if not rows:
        return ""
    lines = []
    for row in rows:
        lines.append(" ".join(str(x) for x in row))
    return "\n".join(lines)


CASES = [
    {"num_rows": 0},
    {"num_rows": 1},
    {"num_rows": 2},
    {"num_rows": 3},
    {"num_rows": 5},
    {"num_rows": 6},
    {"num_rows": 10},
    {"num_rows": 15},
]


def _canonical_output(s):
    """Return a stable canonical string encoding of the output."""
    if s == "":
        return ""
    # Use repr to make newlines explicit and consistent
    return s


if __name__ == "__main__":
    results = []
    for idx, case in enumerate(CASES):
        # Optionally honor the CASE0 env var if present (for the real run),
        # otherwise use the case dict.
        env_val = os.environ.get(f"CASE{idx}")
        if env_val is not None:
            num_rows = int(env_val.strip())
        else:
            num_rows = case["num_rows"]

        out = solve(num_rows)
        results.append({
            "id": idx,
            "input": {"num_rows": num_rows},
            "expected": json.dumps(out, ensure_ascii=False),
        })

    print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))
