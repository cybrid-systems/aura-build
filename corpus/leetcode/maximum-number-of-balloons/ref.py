import json
import os


def solve(text: str) -> int:
    """Return the maximum number of 'balloon's that can be formed from text."""
    if not text:
        return 0
    counts = [0] * 26
    for ch in text:
        counts[ord(ch) - 97] += 1
    b = counts[ord('b') - 97]
    a = counts[ord('a') - 97]
    l = counts[ord('l') - 97] // 2
    o = counts[ord('o') - 97] // 2
    n = counts[ord('n') - 97]
    return min(b, a, l, o, n)


CASES = [
    {"id": 0, "text": "balloonballoon"},
    {"id": 1, "text": "bababnlnonlno"},
    {"id": 2, "text": "zzz"},
    {"id": 3, "text": "balon"},
    {"id": 4, "text": "balloon"},
    {"id": 5, "text": "bbaallllooonn"},
    {"id": 6, "text": "loonbalxballoon"},
    {"id": 7, "text": ""},
]


def _canonical(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False)


def _env_case():
    raw = os.environ.get("CASE0", "")
    if raw.startswith("text="):
        return raw[len("text="):]
    return None


if __name__ == '__main__':
    out = []
    for case in CASES:
        text = case.get("text", "")
        result = solve(text)
        out.append({
            "id": case["id"],
            "input": {"text": text},
            "expected": _canonical(result),
        })

    env_text = _env_case()
    if env_text is not None:
        result = solve(env_text)
        out.append({
            "id": "CASE0",
            "input": {"text": env_text},
            "expected": _canonical(result),
        })

    print(_canonical(out))
