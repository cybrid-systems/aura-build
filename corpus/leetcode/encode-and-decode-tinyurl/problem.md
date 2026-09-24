# Encode and Decode TinyURL

## Problem Statement

Design a simplified URL shortener service (like TinyURL) that supports two operations:

1. **Encode a long URL** into a short URL.
2. **Decode a short URL** back into the original long URL.

You need to implement a service that:
- Takes a long URL and returns a short URL.
- Takes a short URL and returns the original long URL it points to.
- Ensures the mapping is bijective: if URL `A` encodes to short URL `S`, then decoding `S` returns `A`. If the same long URL is encoded multiple times, it should consistently map to the same short URL (or you may generate a fresh one each time — both are acceptable as long as decoding works correctly).

Use a hash map (or similar structure) to store the mappings between long and short URLs.

## Function Signature

```python
class Codec:
    def encode(self, longUrl: str) -> str:
        """Encodes a URL to a shortened URL."""
        ...

    def decode(self, shortUrl: str) -> str:
        """Decodes a shortened URL to its original URL."""
        ...
```

## Input/Output Convention

The harness will exercise your `Codec` class with multiple test cases on a single instance. Each test case is presented as a line on stdin, but since this is an object-oriented design problem, the input is provided via direct method calls on a single `Codec` instance.

For reference, a sample interaction looks like:

```
CASE0=ENCODE https://leetcode.com/problems/design-tinyurl
CASE1=DECODE http://tiny.url/abc123
CASE2=ENCODE https://example.com/very/long/path
```

Each `CASEi` line represents a method invocation:
- `ENCODE <url>` → call `codec.encode(<url>)` and verify the returned short URL can be decoded back to `<url>`.
- `DECODE <shortUrl>` → call `codec.decode(<shortUrl>)` and verify the returned long URL matches the original.

## Notes

- You do not need to implement actual HTTP routing; just the encode/decode logic.
- A common approach: generate a random or counter-based short key for each long URL, and store both `long → short` and `short → long` mappings.
- If the same long URL is encoded twice, either returning the same short URL or a new one each time is acceptable — your decoder must always return the correct original URL for whatever short URL was last produced for it.
- The short URL format is up to you; a simple `"http://tiny.url/" + key` scheme is fine.
