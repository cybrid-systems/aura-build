# Design Browser History

Design a data structure that simulates a web browser's history navigation.

Implement a `BrowserHistory` class with the following methods:

- `BrowserHistory(string homepage)` — Initializes the object with the start page `homepage` as the current page.
- `void visit(string url)` — Visits a new page from the current page. This clears up all forward history.
- `string back(int steps)` — Moves `steps` back in history. Returns the current page after moving (stops at the earliest visited page, i.e., `homepage`).
- `string forward(int steps)` — Moves `steps` forward in history. Returns the current page after moving (stops at the latest visited page).

Assume at least one call will be made to `back` or `forward`.

## Function Signature

```python
class BrowserHistory:
    def __init__(self, homepage: str):
        ...
    def visit(self, url: str) -> None:
        ...
    def back(self, steps: int) -> str:
        ...
    def forward(self, steps: int) -> str:
        ...
```

## Input / Output Convention

The harness drives the class via a `CASE0` directive followed by one operation per line. Each line begins with a token indicating the operation:

- `Visit <url>` → `history.visit(url)`
- `Back <k>` → print `history.back(k)`
- `Forward <k>` → print `history.forward(k)`

The first `Visit <url>` is treated as the `homepage` constructor argument; subsequent lines invoke the corresponding method. Each `Back`/`Forward` line produces one line of output.

Example:

```
CASE0
Visit leetcode.com
Visit google.com
Visit facebook.com
Visit youtube.com
Back 1
Back 1
Forward 1
Visit linkedin.com
Forward 2
Back 2
Back 7
```

Expected output:

```
facebook.com
google.com
facebook.com
linkedin.com
google.com
leetcode.com
```

## Notes

- A doubly linked list is a natural fit; an array of nodes with `prev`/`next` pointers also works.
- `visit` must invalidate all forward history (like a real browser's new navigation).
- `back`/`forward` must clamp to available history; do not raise errors when `steps` exceeds the reachable range.
