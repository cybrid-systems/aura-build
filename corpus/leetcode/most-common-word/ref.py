import re
import json
from collections import Counter


def solve(paragraph, banned):
    banned_set = set(banned)
    # Extract sequences of letters (case-insensitive). The problem says
    # words consist of letters and punctuation should be stripped; using
    # the Unicode-aware regex \w+ works for ASCII letters and may include
    # digits/underscore. To strictly follow "letters only" we use [^\W\d_]+
    # which matches Unicode letters but excludes digits and underscore.
    tokens = re.findall(r'[^\W\d_]+', paragraph, flags=re.UNICODE)
    counter = Counter()
    for token in tokens:
        low = token.lower()
        if low in banned_set:
            continue
        counter[low] += 1
    if not counter:
        return ""
    # most_common returns items sorted by count desc; ties are broken by
    # insertion order in Python's Counter (deterministic enough for judge).
    return counter.most_common(1)[0][0]


CASES = [
    {
        "paragraph": "Bob hit a ball, the hit BALL flew far after it was hit.",
        "banned": ["hit"],
    },
    {
        "paragraph": "a.",
        "banned": [],
    },
    {
        "paragraph": "a, a, a, b, b, c!",
        "banned": ["b"],
    },
    {
        "paragraph": "Hello! Hello!! HELLO...",
        "banned": [],
    },
    {
        "paragraph": "Only banned words here.",
        "banned": ["only", "banned", "words", "here"],
    },
    {
        "paragraph": "",
        "banned": ["x"],
    },
    {
        "paragraph": "Apple, apple, APPLE, banana; BANANA? banana!",
        "banned": [],
    },
    {
        "paragraph": "one two three four five six seven eight nine ten",
        "banned": [],
    },
]


if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["paragraph"], case["banned"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
