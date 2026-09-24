def solve(strs):
    if not strs:
        return ""
    # Find the shortest string length to bound the search
    min_len = min(len(s) for s in strs)
    prefix = []
    for i in range(min_len):
        ch = strs[0][i]
        for s in strs[1:]:
            if s[i] != ch:
                return "".join(prefix)
        prefix.append(ch)
    return "".join(prefix)


CASES = [
    {"CASE0": "flower\nflow\nflight\n"},
    {"CASE0": "dog\nracecar\ncar\n"},
    {"CASE0": "intersect\ninterstate\nintercom\n"},
    {"CASE0": "\n"},
    {"CASE0": "alone\n"},
    {"CASE0": "abc\nabc\nabc\n"},
    {"CASE0": "a\nb\nc\n"},
    {"CASE0": "prefix\nprefab\npresent\npre\n"},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        raw = c["CASE0"]
        strs = raw.split("\n")
        if strs and strs[-1] == "":
            strs = strs[:-1]
        result = solve(strs)
        out.append({"id": i, "input": {"CASE0": raw}, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
