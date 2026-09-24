import json
import sys


def solve(words):
    word_set = set(words)
    words_sorted = sorted(set(words))
    best = ""
    for w in words_sorted:
        valid = True
        for i in range(1, len(w) + 1):
            if w[:i] not in word_set:
                valid = False
                break
        if valid:
            if len(w) > len(best) or (len(w) == len(best) and w < best):
                best = w
    return best


CASES = [
    {"words": ["w", "wo", "wor", "worl", "world"]},
    {"words": ["a", "banana", "app", "appl", "ap", "apply", "apple"]},
    {"words": ["a"]},
    {"words": ["b", "a", "ab"]},
    {"words": ["abc", "ab", "a"]},
    {"words": ["a", "b", "c", "d"]},
    {"words": ["abcd", "abc", "ab", "a", "abce", "abcf"]},
    {"words": ["apple", "apply", "appl", "ap", "a"]},
]


def parse_input(data):
    lines = data.strip().split("\n")
    cases = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("CASE") and "=" in line and ".WORDS" not in line:
            case_id = line.split("=")[0]
            n = int(line.split("=")[1])
            words = []
            j = i + 1
            for k in range(n):
                wl = lines[j].strip()
                _, val = wl.split("=", 1)
                words.append(val)
                j += 1
            cases.append({"id": case_id, "words": words})
            i = j
        else:
            i += 1
    return cases


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "cases"
    if mode == "stdin":
        data = sys.stdin.read()
        cases = parse_input(data)
        results = []
        for c in cases:
            ans = solve(c["words"])
            results.append(ans)
        for r in results:
            print(json.dumps(r, separators=(",", ":"), ensure_ascii=False))
    else:
        results = []
        for idx, c in enumerate(CASES):
            ans = solve(c["words"])
            entry = {"id": idx, "input": c, "expected": json.dumps(ans, separators=(",", ":"), ensure_ascii=False)}
            results.append(entry)
        print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))
