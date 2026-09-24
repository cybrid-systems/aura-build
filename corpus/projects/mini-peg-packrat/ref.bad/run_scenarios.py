#!/usr/bin/env python3
"""
mini-peg-packrat — Python reference implementation.

Simulates the Aura Lisp PEG framework: packrat memoization, left-recursion
detection (seed/recall), semantic actions, combinator API, and an INI grammar
that produces a nested alist of sections/keys.
"""

import sys
from typing import Any, Callable, Optional


# ---------- prelude ----------
def _length(xs):
    n = 0
    for _ in xs:
        n += 1
    return n


def _nth(xs, i):
    return xs[i]


def _take(xs, n):
    return xs[:n]


def _drop(xs, n):
    return xs[n:]


def _reverse_star(xs):
    return list(reversed(xs))


def _append_star(*lists):
    out = []
    for l in lists:
        out.extend(l)
    return out


# ---------- source ----------
class Source:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def new(text: str):
        return Source(text)

    def src_pos(s):
        return s.pos

    def src_eof_p(s):
        return s.pos >= len(s.text)

    def src_peek(s):
        return s.text[s.pos] if not src_eof_p(s) else ""

    def src_rest(s):
        return Source(s.text[s.pos:])

    def src_slice(s, a, b):
        return s.text[a:b]

    def src_len(s):
        return len(s.text)


# ---------- peg/result ----------
class Res:
    def __init__(self, ok, value=None, rest=None):
        self.ok = ok
        self.value = value
        self.rest = rest


def mk_ok(value, rest):
    return Res(True, value, rest)


def mk_fail(rest):
    return Res(False, None, rest)


def res_ok_p(r):
    return r.ok


def res_value(r):
    return r.value


def res_rest(r):
    return r.rest


def res_cons(r, x):
    if not r.ok:
        return r
    return mk_ok([r.value, x] if not isinstance(r.value, list) else r.value + [x], r.rest)


# ---------- peg/memo ----------
class Memo:
    def __init__(self):
        self.table = {}
        self.hits = 0
        self.misses = 0

    def memo_new():
        return Memo()

    def memo_get(m, key):
        if key in m.table:
            m.hits += 1
            return m.table[key]
        m.misses += 1
        return None

    def memo_put(m, key, val):
        m.table[key] = val

    def memo_hits(m):
        return m.hits

    def memo_misses(m):
        return m.misses


# ---------- peg/builder ----------
class Rule:
    def __init__(self, name, body, action=None):
        self.name = name
        self.body = body
        self.action = action
        self.lrec = False

    def rule_new(name, body, action=None):
        return Rule(name, body, action)

    def rule_name(r):
        return r.name

    def rule_body(r):
        return r.body

    def rule_action(r):
        return r.action

    def rule_lrec_p(r):
        return r.lrec

    def rule_mark_lrec(r):
        r.lrec = True


class Grammar:
    def __init__(self):
        self.rules = {}

    def grammar_new():
        return Grammar()

    def grammar_add(g, rule):
        g.rules[rule.name] = rule

    def grammar_get(g, name):
        return g.rules[name]

    def grammar_names(g):
        return list(g.rules.keys())

    def _scan_for_lrec(g, name, body, visiting):
        # body is a tuple; for our INI grammar, nothing is left-recursive.
        # Recursively check for combinators that reference the same rule at the
        # leftmost position without a leading terminator.
        visiting.add(name)
        for item in body:
            tag = item[0]
            if tag == "ref":
                child = item[1]
                if child == name:
                    return True
                if child in visiting:
                    return True
                child_body = g.rules[child].body
                if g._scan_for_lrec(child, child_body, visiting):
                    return True
        visiting.discard(name)
        return False

    def grammar_check_lrec(g):
        for nm, rl in g.rules.items():
            if g._scan_for_lrec(nm, rl.body, set()):
                rl.lrec = True
        # Return 'none' only if no rule is left-recursive
        for rl in g.rules.values():
            if rl.lrec:
                return "found"
        return "none"


Grammar._scan_for_lrec = Grammar._scan_for_lrec


# ---------- peg/parser ----------
_parse_nodes = [0]


def _stats_reset():
    _parse_nodes[0] = 0


def _stats_n_inc():
    _parse_nodes[0] += 1


def stats_nodes():
    return _parse_nodes[0]


def _apply_action(rule, value):
    if rule.action is None:
        return value
    return rule.action(value)


def parse_rule(g, memo, name, src):
    _stats_n_inc()
    key = (name, src.pos)
    cached = memo_get(memo, key)
    if cached is not None:
        return cached
    rule = grammar_get(g, name)
    res = _eval_body(rule.body, g, memo, src)
    val = _apply_action(rule, res_value(res)) if res_ok_p(res) else res
    memo_put(memo, key, val)
    return val


def _eval_body(body, g, memo, src):
    # body is a tuple of combinator items
    # We dispatch on (tag, ...).
    tag = body[0]
    if tag == "seq":
        return _eval_seq(body[1], g, memo, src)
    if tag == "alt":
        return _eval_alt(body[1], g, memo, src)
    if tag == "star":
        return _eval_star(body[1], g, memo, src)
    if tag == "plus":
        return _eval_plus(body[1], g, memo, src)
    if tag == "opt":
        return _eval_opt(body[1], g, memo, src)
    if tag == "token":
        return _eval_token(body[1], src)
    if tag == "any":
        return _eval_any(src)
    if tag == "satisfies":
        return _eval_satisfies(body[1], src)
    if tag == "between":
        return _eval_between(body[1], body[2], body[3], g, memo, src)
    if tag == "sep_by":
        return _eval_sep_by(body[1], body[2], g, memo, src)
    if tag == "ref":
        return parse_rule(g, memo, body[1], src)
    if tag == "empty":
        return mk_ok(None, src)
    return mk_fail(src)


def _eval_seq(items, g, memo, src):
    vals = []
    cur = src
    for it in items:
        r = _eval_body(it, g, memo, cur)
        if not res_ok_p(r):
            return mk_fail(src)
        vals.append(res_value(r))
        cur = res_rest(r)
    return mk_ok(vals, cur)


def _eval_alt(alts, g, memo, src):
    for a in alts:
        r = _eval_body(a, g, memo, src)
        if res_ok_p(r):
            return r
    return mk_fail(src)


def _eval_star(item, g, memo, src):
    vals = []
    cur = src
    while True:
        r = _eval_body(item, g, memo, cur)
        if not res_ok_p(r):
            break
        vals.append(res_value(r))
        cur = res_rest(r)
        if cur.pos == src.pos and not res_ok_p(r):
            break
        # prevent infinite loop on zero-progress
        if not res_ok_p(r):
            break
        # safety: if rest didn't advance AND we matched, break
        if res_rest(r).pos == _last_pos(cur) and len(vals) > 0 and cur.pos == src.pos:
            break
        # update src reference for outer loop
        if cur.pos == src.pos and len(vals) > 0:
            # matched but no progress (shouldn't happen in well-formed grammar)
            break
        src = cur
    return mk_ok(vals, cur)


def _last_pos(s):
    return s.pos


def _eval_plus(item, g, memo, src):
    r1 = _eval_body(item, g, memo, src)
    if not res_ok_p(r1):
        return mk_fail(src)
    rest_res = _eval_star(item, g, memo, res_rest(r1))
    return mk_ok([res_value(r1)] + (res_value(rest_res) or []), res_rest(rest_res))


def _eval_opt(item, g, memo, src):
    r = _eval_body(item, g, memo, src)
    if res_ok_p(r):
        return mk_ok(res_value(r), res_rest(r))
    return mk_ok(None, src)


def _eval_token(tok, src):
    if src.text.startswith(tok, src.pos):
        return mk_ok(tok, Source(src.text))
        # need to return rest with pos advanced
    new_src = Source(src.text)
    new_src.pos = src.pos + len(tok)
    if src.text[src.pos:src.pos + len(tok)] == tok:
        return mk_ok(tok, new_src)
    return mk_fail(src)


def _eval_any(src):
    if src_eof_p(src):
        return mk_fail(src)
    c = src_peek(src)
    new_src = Source(src.text)
    new_src.pos = src.pos + 1
    return mk_ok(c, new_src)


def _eval_satisfies(pred, src):
    if src_eof_p(src):
        return mk_fail(src)
    c = src_peek(src)
    if pred(c):
        new_src = Source(src.text)
        new_src.pos = src.pos + 1
        return mk_ok(c, new_src)
    return mk_fail(src)


def _eval_between(open_b, item, close_b, g, memo, src):
    r1 = _eval_body(open_b, g, memo, src)
    if not res_ok_p(r1):
        return mk_fail(src)
    r2 = _eval_body(item, g, memo, res_rest(r1))
    if not res_ok_p(r2):
        return mk_fail(src)
    r3 = _eval_body(close_b, g, memo, res_rest(r2))
    if not res_ok_p(r3):
        return mk_fail(src)
    return mk_ok(res_value(r2), res_rest(r3))


def _eval_sep_by(item, sep, g, memo, src):
    vals = []
    cur = src
    r = _eval_body(item, g, memo, cur)
    if not res_ok_p(r):
        return mk_ok([], cur)
    vals.append(res_value(r))
    cur = res_rest(r)
    while True:
        rs = _eval_body(sep, g, memo, cur)
        if not res_ok_p(rs):
            break
        ri = _eval_body(item, g, memo, res_rest(rs))
        if not res_ok_p(ri):
            break
        vals.append(res_value(ri))
        cur = res_rest(ri)
    return mk_ok(vals, cur)


# Fix _eval_token: it was wrong above, redo
def _eval_token(tok, src):
    if src.text[src.pos:src.pos + len(tok)] == tok:
        new_src = Source(src.text)
        new_src.pos = src.pos + len(tok)
        return mk_ok(tok, new_src)
    return mk_fail(src)


# ---------- combinator helpers (for grammar construction) ----------
def peg_seq(*items):
    return ("seq", items)


def peg_alt(*alts):
    return ("alt", alts)


def peg_star(item):
    return ("star", item)


def peg_plus(item):
    return ("plus", item)


def peg_opt(item):
    return ("opt", item)


def peg_token(s):
    return ("token", s)


def peg_any():
    return ("any",)


def peg_satisfies(pred):
    return ("satisfies", pred)


def peg_between(o, x, c):
    return ("between", o, x, c)


def peg_sep_by(item, sep):
    return ("sep_by", item, sep)


def peg_action(item, fn):
    # Wrap an item with a post-action
    return ("action", item, fn)


# Override _eval_body to handle action
_orig_eval_body = _eval_body


def _eval_body(body, g, memo, src):
    tag = body[0]
    if tag == "action":
        r = _orig_eval_body(body[1], g, memo, src)
        if not res_ok_p(r):
            return r
        return mk_ok(body[2](res_value(r)), res_rest(r))
    return _orig_eval_body(body, g, memo, src)


def parse_grammar(g, memo, start, src):
    r = parse_rule(g, memo, start, src)
    if res_ok_p(r) and src_eof_p(res_rest(r)):
        return res_value(r)
    return None


# ---------- INI grammar ----------
INI_SAMPLE = """; sample config
app_name = aura-peg
version = 1.0

[db]
host = localhost
port = 5432
user = admin

[server]
host = 0.0.0.0
port = 8080

[logging]
level = info
file = /var/log/aura.log
"""


def ini_tokenize(text):
    # Char-level line splitter; returns list of lines.
    return text.split("\n")


def ini_build_grammar():
    g = grammar_new()

    # ws := (';' line*) | (' ' | '\t')*
    line_rest = peg_star(peg_satisfies(lambda c: c != "\n"))
    comment = peg_seq(peg_token(";"), line_rest)
    space = peg_satisfies(lambda c: c == " " or c == "\t" or c == "\r")
    ws = peg_alt(("body", comment), ("body2", peg_star(space)))

    # ident := [a-zA-Z_][a-zA-Z0-9_]*
    ident_first = peg_satisfies(lambda c: c.isalpha() or c == "_")
    ident_rest = peg_star(peg_satisfies(lambda c: c.isalnum() or c == "_"))
    ident = peg_seq(("item1", ident_first), ("item2", ident_rest))

    # value := rest of line until newline
    value_char = peg_satisfies(lambda c: c != "\n")
    value = peg_plus(value_char)

    # key := ws* ident ws* '=' ws* value
    eq = peg_token("=")
    key = peg_seq(
        ("a", peg_star(("w", ("ref", "ws")))),
        ("b", ("ref", "ident")),
        ("c", peg_star(("w2", ("ref", "ws")))),
        ("d", eq),
        ("e", peg_star(("w3", ("ref", "ws")))),
        ("f", ("ref", "value")),
    )

    # section := ws* '[' ident ']' ws* '\n'
    section = peg_seq(
        ("a", peg_star(("w", ("ref", "ws")))),
        ("b", peg_token("[")),
        ("c", ("ref", "ident")),
        ("d", peg_token("]")),
        ("e", peg_star(("w2", ("ref", "ws")))),
    )

    # ini := (section | key)*
    entry = peg_alt(("s", ("ref", "section")), ("k", ("ref", "key")))
    ini = peg_star(entry)

    grammar_add(g, rule_new("ws", ws))
    grammar_add(g, rule_new("ident", ident))
    grammar_add(g, rule_new("value", value))
    grammar_add(g, rule_new("key", key, action=lambda v: _ini_key_action(v)))
    grammar_add(g, rule_new("section", section, action=lambda v: _ini_section_action(v)))
    grammar_add(g, rule_new("ini", ini))
    return g


def _flatten_seq_vals(v):
    # Walk a nested seq tree produced by peg_seq, returning the list of values
    # of the inner items in order.
    out = []
    if isinstance(v, list):
        for x in v:
            if isinstance(x, list):
                out.extend(_flatten_seq_vals(x))
            else:
                out.append(x)
    else:
        out.append(v)
    return out


def _ini_key_action(v):
    flat = _flatten_seq_vals(v)
    # flat layout: [ws*, ident_str, ws*, '=', ws*, value_chars_list]
    ident = None
    value_chars = None
    for x in flat:
        if isinstance(x, str):
            if ident is None and x not in (" ", "\t", "\r", "=", "\n"):
                # skip if it's the '=' literal
                if x == "=":
                    continue
                if ident is None:
                    ident = x
                    continue
            if x == "=":
                continue
        if isinstance(x, list):
            value_chars = x
    if value_chars is None:
        # value might be a string already
        value_chars = []
    val_str = "".join(value_chars) if isinstance(value_chars, list) else str(value_chars)
    return ["__key__", ident, val_str]


def _ini_section_action(v):
    flat = _flatten_seq_vals(v)
    name = None
    for x in flat:
        if isinstance(x, str) and x not in ("[", "]", " ", "\t", "\r"):
            name = x
            break
    return ["__section__", name]


# Override _eval_seq to call rule actions per matched item: actually we already
# apply rule-level actions. For seq items that are refs to rules with actions,
# the parse_rule call applies the action automatically. Good.


def ini_parse(source, grammar):
    _stats_reset()
    memo = memo_new()
    src = source
    result = parse_rule(grammar, memo, "ini", src)
    if res_ok_p(result):
        return res_value(result), memo
    return [], memo


def ini_sections(alist):
    secs = []
    for entry in alist:
        if isinstance(entry, list) and len(entry) >= 1 and entry[0] == "__section__":
            secs.append(entry[1])
    return secs


def ini_flat_keys(alist):
    keys = []
    for entry in alist:
        if isinstance(entry, list) and len(entry) >= 1 and entry[0] == "__key__":
            keys.append(entry[1])
    return keys


def ini_get(alist, section, key):
    current = None
    for entry in alist:
        if isinstance(entry, list) and len(entry) >= 1:
            if entry[0] == "__section__":
                current = entry[1]
            elif entry[0] == "__key__" and current == section and entry[1] == key:
                return entry[2]
    return None


# ---------- main ----------
def main():
    # Step 1-2: source
    src = Source.new(INI_SAMPLE)

    # Step 3: build grammar
    grammar = ini_build_grammar()

    # Step 4: left recursion check
    lrec_status = grammar_check_lrec(grammar)

    # Step 5: parse
    alist, memo = ini_parse(src, grammar)

    # Step 6: walk alist
    sections = ini_sections(alist)
    flat_keys = ini_flat_keys(alist)

    # Step 7: print KEY=value lines
    print(f"PARSER=mini-peg-packrat")
    print(f"GRAMMAR=ini")
    print(f"INPUT_BYTES={src_len(src)}")
    print(f"LEFT_RECURSIVE={lrec_status}")
    print(f"MEMO_HITS={memo_hits(memo)}")
    print(f"MEMO_MISSES={memo_misses(memo)}")
    print(f"NODES={stats_nodes()}")
    print(f"OK_SECTIONS={_length(sections)}")
    print(f"OK_KEYS={_length(flat_keys)}")
    print(f"SEM_DB_HOST={ini_get(alist, 'db', 'host')}")
    print(f"SEM_DB_PORT={ini_get(alist, 'db', 'port')}")
    print(f"SEM_APP_NAME={ini_get(alist, 'app_name', None) or _ini_get_top(alist, 'app_name')}")


def _ini_get_top(alist, key):
    """Get a top-level (pre-section) key like app_name."""
    current = "__top__"
    for entry in alist:
        if isinstance(entry, list) and len(entry) >= 1:
            if entry[0] == "__section__":
                current = entry[1]
            elif entry[0] == "__key__" and current == "__top__" and entry[1] == key:
                return entry[2]
    return None


if __name__ == "__main__":
    main()
