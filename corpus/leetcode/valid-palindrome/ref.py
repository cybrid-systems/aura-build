import json

def solve(s: str) -> bool:
    if not isinstance(s, str):
        s = str(s)
    filtered = ''.join(ch.lower() for ch in s if ch.isalnum())
    return filtered == filtered[::-1]

CASES = [
    {"s": "A man, a plan, a canal: Panama"},
    {"s": "race a car"},
    {"s": " "},
    {"s": "0P"},
    {"s": ""},
    {"s": "abba"},
    {"s": "abc"},
    {"s": "Was it a car or a cat I saw?"},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        args = {k: v for k, v in case.items()}
        result = solve(**args)
        results.append({
            "id": i,
            "input": args,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
