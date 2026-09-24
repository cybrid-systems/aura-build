import json

def solve(secret: str, guess: str) -> tuple[int, int]:
    bulls = 0
    s_freq = [0] * 10
    g_freq = [0] * 10
    for s, g in zip(secret, guess):
        if s == g:
            bulls += 1
        else:
            s_freq[ord(s) - 48] += 1
            g_freq[ord(g) - 48] += 1
    cows = sum(min(s_freq[d], g_freq[d]) for d in range(10))
    return (bulls, cows)

CASES = [
    {"secret": "1807", "guess": "7810"},
    {"secret": "1123", "guess": "0111"},
    {"secret": "0123", "guess": "0123"},
    {"secret": "0000", "guess": "1111"},
    {"secret": "1234", "guess": "4321"},
    {"secret": "9999", "guess": "9999"},
    {"secret": "102030405060708090", "guess": "001122334455667788"},
    {"secret": "111111", "guess": "111111"},
    {"secret": "0123456789", "guess": "9876543210"},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["secret"], c["guess"])
        out.append({
            "id": i,
            "input": {"secret": c["secret"], "guess": c["guess"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
