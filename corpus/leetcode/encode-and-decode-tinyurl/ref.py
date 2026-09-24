class Codec:
    def __init__(self):
        self.long_to_short = {}
        self.short_to_long = {}
        self.counter = 0
        self.base = "http://tiny.url/"

    def encode(self, longUrl: str) -> str:
        if longUrl in self.long_to_short:
            return self.long_to_short[longUrl]
        self.counter += 1
        key = str(self.counter)
        short = self.base + key
        self.long_to_short[longUrl] = short
        self.short_to_long[short] = longUrl
        return short

    def decode(self, shortUrl: str) -> str:
        return self.short_to_long.get(shortUrl, "")


def solve(codec, operations):
    results = []
    for op in operations:
        if op["type"] == "ENCODE":
            results.append(codec.encode(op["url"]))
        elif op["type"] == "DECODE":
            results.append(codec.decode(op["url"]))
    return results


CASES = [
    {"operations": [
        {"type": "ENCODE", "url": "https://leetcode.com/problems/design-tinyurl"},
    ]},
    {"operations": [
        {"type": "ENCODE", "url": "https://example.com/very/long/path"},
        {"type": "ENCODE", "url": "https://example.com/very/long/path"},
        {"type": "ENCODE", "url": "https://another.com"},
    ]},
    {"operations": [
        {"type": "ENCODE", "url": "https://a.com"},
        {"type": "ENCODE", "url": "https://b.com"},
        {"type": "ENCODE", "url": "https://c.com"},
    ]},
    {"operations": [
        {"type": "DECODE", "url": "http://tiny.url/1"},
    ]},
    {"operations": [
        {"type": "ENCODE", "url": "https://x.com"},
        {"type": "DECODE", "url": "http://tiny.url/1"},
    ]},
    {"operations": [
        {"type": "ENCODE", "url": "https://test.com/path?query=1"},
        {"type": "ENCODE", "url": "https://test.com/path?query=2"},
        {"type": "ENCODE", "url": "https://test.com/path?query=1"},
    ]},
    {"operations": []},
    {"operations": [
        {"type": "ENCODE", "url": "https://single.com"},
        {"type": "ENCODE", "url": "https://single.com"},
        {"type": "ENCODE", "url": "https://single.com"},
    ]},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        codec = Codec()
        result = solve(codec, case["operations"])
        out.append({"id": idx, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
