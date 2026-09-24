#!/usr/bin/env python3
"""Reference Python implementation of the mini-json-tok Aura project GOAL.

This script implements the same in-memory semantics as the 11-file Aura
project described in GOAL.md: a zero-copy UTF-8 tokenizer, tolerant JSON
parser, structural index builder, streaming event emitter, and a lenient
recovery pass.  Every key in the GOAL "expect" list is computed by walking
the same data through the same toy APIs the Aura modules export.
"""

from __future__ import annotations

import sys
from typing import Any, Iterable, List, Tuple


# ---------------------------------------------------------------------------
# Module 1: utf8.aura -- minimal UTF-8 helpers (in-memory, no real codec).
# ---------------------------------------------------------------------------

def utf8_byte_len(b: int) -> int:
    """Return the expected UTF-8 sequence length for leading byte ``b``."""
    if b < 0x80:
        return 1
    if b < 0xC0:
        return 0  # stray continuation byte
    if b < 0xE0:
        return 2
    if b < 0xF0:
        return 3
    return 4


def utf8_bom_skip(src: str, i: int) -> int:
    """Skip an optional BOM (\\ufeff at the head of ``src``)."""
    if i == 0 and src.startswith("\ufeff"):
        return 1
    return i


def utf8_validate(src: str) -> bool:
    """Strings in our toy model are always valid UTF-8 once decoded."""
    # All inputs are Python str (already decoded), so always valid.
    return True


# ---------------------------------------------------------------------------
# Module 2: json-lex.aura -- zero-copy tokenizer.
# ---------------------------------------------------------------------------

# Token kinds: 'string 'number', 'bool', 'null', 'lbrace', 'rbrace',
#              'lbracket', 'rbracket', 'comma', 'colon'.

def lex_tokenize(src: str) -> List[Tuple[str, Tuple[int, int], Any]]:
    """Tokenize ``src`` into a flat list of (kind, (start, end), value) tuples."""
    tokens: List[Tuple[str, Tuple[int, int], Any]] = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == " " or c == "\t" or c == "\n" or c == "\r":
            i += 1
            continue
        start = i
        if c == "{":
            tokens.append(("lbrace", (start, i + 1), None))
            i += 1
        elif c == "}":
            tokens.append(("rbrace", (start, i + 1), None))
            i += 1
        elif c == "[":
            tokens.append(("lbracket", (start, i + 1), None))
            i += 1
        elif c == "]":
            tokens.append(("rbracket", (start, i + 1), None))
            i += 1
        elif c == ",":
            tokens.append(("comma", (start, i + 1), None))
            i += 1
        elif c == ":":
            tokens.append(("colon", (start, i + 1), None))
            i += 1
        elif c == '"':
            j = i + 1
            while j < n:
                if src[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if src[j] == '"':
                    break
                j += 1
            end = j + 1 if j < n else n
            raw = src[i:end]
            # Unescape minimally for the value (used by ast step).
            value = bytes(raw, "utf-8").decode("unicode_escape", errors="ignore")
            tokens.append(("string", (start, end), value))
            i = end
        elif c == "-" or c.isdigit():
            j = i + 1
            seen_dot = False
            seen_exp = False
            while j < n and (src[j].isdigit() or src[j] in ".eE+-"):
                if src[j] == ".":
                    if seen_dot:
                        break
                    seen_dot = True
                elif src[j] in "eE":
                    if seen_exp:
                        break
                    seen_exp = True
                j += 1
            try:
                value = float(src[i:j])
                if value.is_integer() and abs(value) < 1e18:
                    value = int(value)
            except Exception:
                value = src[i:j]
            tokens.append(("number", (start, j), value))
            i = j
        elif src.startswith("true", i):
            tokens.append(("bool", (start, i + 4), True))
            i += 4
        elif src.startswith("false", i):
            tokens.append(("bool", (start, i + 5), False))
            i += 5
        elif src.startswith("null", i):
            tokens.append(("null", (start, i + 4), None))
            i += 4
        else:
            # Unknown character: stop lexing, the rest is "trailing garbage".
            break
    return tokens


def token_kind(tok: Tuple[str, Tuple[int, int], Any]) -> str:
    return tok[0]


def token_span(tok: Tuple[str, Tuple[int, int], Any]) -> Tuple[int, int]:
    return tok[1]


def token_value(tok: Tuple[str, Tuple[int, int], Any]) -> Any:
    return tok[2]


# ---------------------------------------------------------------------------
# Module 3: json-ast.aura -- tolerant recursive-descent parser.
# ---------------------------------------------------------------------------

def parse_json(src: str) -> Any:
    """Parse ``src``.  Returns either an AST node tuple, or an error dict
    produced via ``make_error`` (see json-errors)."""
    tokens = lex_tokenize(src)
    pos = 0

    def peek() -> str:
        return tokens[pos][0] if pos < len(tokens) else "eof"

    def advance() -> Tuple[str, Tuple[int, int], Any]:
        nonlocal pos
        if pos >= len(tokens):
            err = make_error("E_EOF", len(src), "unexpected end of input")
            raise _ParseFailure(err)
        tok = tokens[pos]
        pos += 1
        return tok

    def parse_value() -> Any:
        kind = peek()
        if kind == "lbrace":
            return parse_object()
        if kind == "lbracket":
            return parse_array()
        if kind == "string":
            tok = advance()
            return ("string", [], token_value(tok))
        if kind == "number":
            tok = advance()
            return ("number", [], token_value(tok))
        if kind == "bool":
            tok = advance()
            return ("bool", [], token_value(tok))
        if kind == "null":
            tok = advance()
            return ("null", [], None)
        err = make_error("E_PARSE", len(src), f"unexpected token {kind}")
        raise _ParseFailure(err)

    def parse_object() -> Any:
        advance()  # lbrace
        keys: List[Any] = []
        if peek() == "rbrace":
            advance()
            return ("object", [], {})
        while True:
            if peek() != "string":
                err = make_error("E_KEY", len(src), "expected string key")
                raise _ParseFailure(err)
            key_tok = advance()
            key = token_value(key_tok)
            if peek() != "colon":
                err = make_error("E_COLON", len(src), "expected ':'")
                raise _ParseFailure(err)
            advance()
            val = parse_value()
            keys.append((key, val))
            if peek() == "comma":
                advance()
                continue
            if peek() == "rbrace":
                advance()
                return ("object", [], keys)
            err = make_error("E_OBJ", len(src), "expected ',' or '}'")
            raise _ParseFailure(err)

    def parse_array() -> Any:
        advance()  # lbracket
        elems: List[Any] = []
        if peek() == "rbracket":
            advance()
            return ("array", [], elems)
        while True:
            elems.append(parse_value())
            if peek() == "comma":
                advance()
                continue
            if peek() == "rbracket":
                advance()
                return ("array", [], elems)
            err = make_error("E_ARR", len(src), "expected ',' or ']'")
            raise _ParseFailure(err)

    try:
        # BOM skip for parity with utf8.aura usage in scenario.aura.
        utf8_bom_skip(src, 0)
        node = parse_value()
        return node
    except _ParseFailure as pf:
        return pf.error


class _ParseFailure(Exception):
    def __init__(self, error: dict):
        self.error = error


def ast_kind(node: Any) -> str:
    if isinstance(node, dict) and node.get("__error__"):
        return "error"
    return node[0]


def ast_children(node: Any) -> List[Any]:
    if isinstance(node, dict) and node.get("__error__"):
        return []
    return node[1] if len(node) > 1 else []


def ast_value(node: Any) -> Any:
    if isinstance(node, dict) and node.get("__error__"):
        return None
    return node[2] if len(node) > 2 else None


# ---------------------------------------------------------------------------
# Module 4: json-index.aura -- structural index over an AST.
# ---------------------------------------------------------------------------

def build_index(node: Any) -> dict:
    """Walk the AST and produce an index: depth, and counts per kind."""
    idx = {"max_depth": 0, "objects": 0, "arrays": 0, "strings": 0,
           "numbers": 0, "bools": 0, "nulls": 0, "nodes": []}

    def walk(n: Any, depth: int) -> None:
        if depth > idx["max_depth"]:
            idx["max_depth"] = depth
        if isinstance(n, dict) and n.get("__error__"):
            return
        kind = ast_kind(n)
        if kind == "object":
            idx["objects"] += 1
        elif kind == "array":
            idx["arrays"] += 1
        elif kind == "string":
            idx["strings"] += 1
        elif kind == "number":
            idx["numbers"] += 1
        elif kind == "bool":
            idx["bools"] += 1
        elif kind == "null":
            idx["nulls"] += 1
        idx["nodes"].append(n)
        for child in ast_children(n):
            walk(child, depth + 1)

    walk(node, 1)
    return idx


def index_depth(idx: dict) -> int:
    return idx["max_depth"]


def index_count(idx: dict, kind: str) -> int:
    if kind == "object":
        return idx["objects"]
    if kind == "array":
        return idx["arrays"]
    if kind == "string":
        return idx["strings"]
    if kind == "number":
        return idx["numbers"]
    if kind == "bool":
        return idx["bools"]
    if kind == "null":
        return idx["nulls"]
    return 0


def index_walk(idx: dict, proc) -> None:
    for n in idx["nodes"]:
        proc(n)


# ---------------------------------------------------------------------------
# Module 5: json-stream.aura -- streaming events with paths.
# ---------------------------------------------------------------------------

def stream_events(src: str) -> List[Tuple[str, Tuple[Any, ...], int]]:
    """Emit (kind, path, depth) events as we walk the AST."""
    events: List[Tuple[str, Tuple[Any, ...], int]] = []
    node = parse_json(src)
    if isinstance(node, dict) and node.get("__error__"):
        return events

    def walk(n: Any, path: Tuple[Any, ...], depth: int) -> None:
        if isinstance(n, dict) and n.get("__error__"):
            return
        kind = ast_kind(n)
        if kind == "object":
            events.append(("object", path, depth))
            for k, v in ast_children(n):
                walk(v, path + ("key", k), depth + 1)
        elif kind == "array":
            events.append(("array", path, depth))
            for idx, v in enumerate(ast_children(n)):
                walk(v, path + ("index", idx), depth + 1)
        elif kind == "string":
            events.append(("string", path, depth))
        elif kind == "number":
            events.append(("number", path, depth))
        elif kind == "bool":
            events.append(("bool", path, depth))
        elif kind == "null":
            events.append(("null", path, depth))

    walk(node, (), 1)
    return events


def event_kind(ev: Tuple[str, Tuple[Any, ...], int]) -> str:
    return ev[0]


def event_path(ev: Tuple[str, Tuple[Any, ...], int]) -> Tuple[Any, ...]:
    return ev[1]


def event_depth(ev: Tuple[str, Tuple[Any, ...], int]) -> int:
    return ev[2]


# ---------------------------------------------------------------------------
# Module 6: json-recover.aura -- lenient recovery of trailing garbage.
# ---------------------------------------------------------------------------

def recover_lenient(src: str) -> dict:
    """Try to parse ``src``; if there's trailing garbage or a truncation,
    return a recovery descriptor with a status of 'recovered' or
    'truncated'."""
    tokens = lex_tokenize(src)
    # Find the largest prefix of tokens yielding a complete value.
    best_end = -1
    for cut in range(len(tokens), 0, -1):
        sub_tokens = tokens[:cut]
        sub_src = _slice_by_tokens(src, sub_tokens)
        try:
            _silent_parse(sub_src)
            best_end = sub_tokens[-1][1][1] if sub_tokens else 0
            break
        except _ParseFailure:
            continue
    if best_end == -1:
        # Could not parse anything -- try the "truncated" path by scanning
        # for an unfinished string at the tail.
        truncated = _looks_truncated(src)
        if truncated:
            return {"status": "truncated", "bytes_used": truncated,
                    "ast": ("error", [], None)}
        return {"status": "truncated", "bytes_used": 0,
                "ast": ("error", [], None)}
    trailing = src[best_end:].strip()
    if trailing == "":
        # Full clean parse.
        ast = parse_json(src)
        return {"status": "ok", "bytes_used": best_end, "ast": ast}
    return {"status": "recovered", "bytes_used": best_end,
            "ast": parse_json(src[:best_end])}


def recovery_status(r: dict) -> str:
    return r["status"]


def recovery_bytes_used(r: dict) -> int:
    return r["bytes_used"]


def recovery_ast(r: dict) -> Any:
    return r["ast"]


def _slice_by_tokens(src: str, tokens) -> str:
    if not tokens:
        return ""
    return src[: tokens[-1][1][1]]


def _silent_parse(src: str) -> None:
    try:
        node = parse_json(src)
        if isinstance(node, dict) and node.get("__error__"):
            raise _ParseFailure(node)
    except _ParseFailure:
        raise


def _looks_truncated(src: str) -> int:
    """If the source ends with an unterminated string, return its start."""
    # Walk through src finding a string opener without a closer.
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == "{" or c == "[" or c == "," or c == ":" or c == " " \
                or c == "\t" or c == "\n" or c == "\r":
            i += 1
            continue
        if c == '"':
            # find matching close
            j = i + 1
            while j < n:
                if src[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if src[j] == '"':
                    return 0
                j += 1
            return i
        # Numbers / literals / closing braces: not a truncation.
        return 0
    return 0


# ---------------------------------------------------------------------------
# Module 7: json-path.aura -- tiny path helpers (used by stream test).
# ---------------------------------------------------------------------------

def path_equal(a, b) -> bool:
    return tuple(a) == tuple(b)


def path_prepend(p, k) -> Tuple[Any, ...]:
    return (k,) + tuple(p)


def path_key(p):
    if len(p) >= 2 and p[0] == "key":
        return p[1]
    return None


def path_index(p):
    if len(p) >= 2 and p[0] == "index":
        return p[1]
    return None


# ---------------------------------------------------------------------------
# Module 8: json-errors.aura -- error record helpers.
# ---------------------------------------------------------------------------

def make_error(code: str, pos: int, msg: str) -> dict:
    return {"__error__": True, "code": code, "pos": pos, "msg": msg}


def error_is(v: Any) -> bool:
    return isinstance(v, dict) and bool(v.get("__error__"))


def error_code(e: dict) -> str:
    return e.get("code", "")


def error_pos(e: dict) -> int:
    return e.get("pos", 0)


# ---------------------------------------------------------------------------
# Module 9: counts.aura -- generic list helpers.
# ---------------------------------------------------------------------------

def count_by_kind(tokens, kinds: List[str]) -> int:
    """Count tokens whose kind is in ``kinds``."""
    return sum(1 for t in tokens if token_kind(t) in kinds)


def sum_list(lst: Iterable[float]) -> float:
    total = 0
    for x in lst:
        total += x
    return total


def every(p, lst: Iterable[Any]) -> bool:
    for x in lst:
        if not p(x):
            return False
    return True


def max_depth(nodes: List[Any]) -> int:
    best = 0
    for n in nodes:
        d = _node_depth(n, 1)
        if d > best:
            best = d
    return best


def _node_depth(n: Any, depth: int) -> int:
    if isinstance(n, dict) and n.get("__error__"):
        return depth
    kids = ast_children(n)
    if not kids:
        return depth
    best = depth
    for c in kids:
        d = _node_depth(c, depth + 1)
        if d > best:
            best = d
    return best


# ---------------------------------------------------------------------------
# Module 10: scenario.aura -- the orchestration entry point.
# ---------------------------------------------------------------------------

DOC_A = '{"name":"ada","age":36,"skills":["math","cs"]}'
DOC_B = '[1,2,3,4,5]'
DOC_C = '{"nested":{"a":1,"b":[true,false,null,"end"]}}'
DOC_GARBAGE = '{"x":1}garbage tail'
DOC_TRUNC = '{"only":"half'


def run_scenario() -> List[Tuple[str, Any]]:
    results: List[Tuple[str, Any]] = []

    # --- utf8 exercise ---
    sample_bytes = [ord(src_doc_first(DOC_A)) & 0xFF for _ in range(1)]
    _ = utf8_byte_len(sample_bytes[0])
    _ = utf8_bom_skip(DOC_A, 0)
    _ = utf8_validate(DOC_A)

    # --- tokenize doc A ---
    tokens = lex_tokenize(DOC_A)
    total = len(tokens)
    n_string = count_by_kind(tokens, ["string"])
    n_number = count_by_kind(tokens, ["number"])
    n_bool_null = count_by_kind(tokens, ["bool", "null"])
    n_struct = count_by_kind(tokens, ["lbrace", "rbrace", "lbracket",
                                      "rbracket"])
    results.append(("TOK_KIND_TOTAL", total))
    results.append(("TOK_KIND_STRING", n_string))
    results.append(("TOK_KIND_NUMBER", n_number))
    results.append(("TOK_KIND_BOOL_NULL", n_bool_null))
    results.append(("TOK_KIND_STRUCT", n_struct))

    # --- parse A, B, C ---
    ok = 0
    fail = 0
    for doc in (DOC_A, DOC_B, DOC_C):
        node = parse_json(doc)
        if error_is(node):
            fail += 1
        else:
            ok += 1
    results.append(("TOK_PARSE_OK_DOCS", ok))
    results.append(("TOK_PARSE_FAIL_DOCS", fail))

    # --- index of C ---
    ast_c = parse_json(DOC_C)
    idx = build_index(ast_c)
    results.append(("TOK_INDEX_DEPTH_MAX", index_depth(idx)))
    results.append(("TOK_INDEX_OBJECT_KEYS", index_count(idx, "object")))
    results.append(("TOK_INDEX_ARRAY_ELS", index_count(idx, "array")))

    # --- stream events over A ---
    events = stream_events(DOC_A)
    kinds = [event_kind(e) for e in events]
    results.append(("TOK_STREAM_EVENTS", len(events)))
    results.append(("TOK_STREAM_HAS_STRING", "string" in kinds))
    results.append(("TOK_STREAM_HAS_NUMBER", "number" in kinds))
    results.append(("TOK_STREAM_HAS_BOOL", "bool" in kinds))
    results.append(("TOK_STREAM_HAS_NULL", "null" in kinds))

    # --- lenient recovery ---
    r1 = recover_lenient(DOC_GARBAGE)
    r2 = recover_lenient(DOC_TRUNC)
    recovered = 0
    truncated = 0
    for r in (r1, r2):
        st = recovery_status(r)
        if st == "recovered":
            recovered += 1
        elif st == "truncated":
            truncated += 1
    results.append(("TOK_LENIENT_RECOVERED", recovered))
    results.append(("TOK_LENIENT_TRUNCATED", truncated))

    return results


def src_doc_first(s: str) -> str:
    return s[0] if s else "\x00"


# ---------------------------------------------------------------------------
# Module 11: main.aura -- print results in the exact required order.
# ---------------------------------------------------------------------------

KEY_ORDER = [
    "TOK_KIND_TOTAL",
    "TOK_KIND_STRING",
    "TOK_KIND_NUMBER",
    "TOK_KIND_BOOL_NULL",
    "TOK_KIND_STRUCT",
    "TOK_PARSE_OK_DOCS",
    "TOK_PARSE_FAIL_DOCS",
    "TOK_INDEX_DEPTH_MAX",
    "TOK_INDEX_OBJECT_KEYS",
    "TOK_INDEX_ARRAY_ELS",
    "TOK_STREAM_EVENTS",
    "TOK_STREAM_HAS_STRING",
    "TOK_STREAM_HAS_NUMBER",
    "TOK_STREAM_HAS_BOOL",
    "TOK_STREAM_HAS_NULL",
    "TOK_LENIENT_RECOVERED",
    "TOK_LENIENT_TRUNCATED",
]


def _format(v: Any) -> str:
    if v is True:
        return "#t"
    if v is False:
        return "#f"
    if isinstance(v, bool):
        return "#t" if v else "#f"
    return str(v)


def main() -> int:
    results = run_scenario()
    by_key = {k: v for k, v in results}
    out_lines = []
    for k in KEY_ORDER:
        out_lines.append(f"{k}={_format(by_key[k])}")
    sys.stdout.write("\n".join(out_lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
