#!/usr/bin/env python3
"""Reference implementation for mini-recv-descent (Aura recursive descent parser).

Implements toy in-memory semantics for the scenario: lexer, AST, precedence,
parser (recursive descent with precedence climbing for */+-, error recovery
via panic-mode at ; and EOF), pretty-printer with round-trip stability,
and prints 12 KEY=value lines on stdout.
"""

from __future__ import annotations
import sys
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any


# ----------------------------- token.aura -----------------------------
@dataclass
class Token:
    type: str     # 'num, 'id, '+, '-, '*, '/, '(, '), 'let, ';, '=, 'eof
    lexeme: str
    line: int
    col: int


def make_token(type_: str, lexeme: str, line: int, col: int) -> Token:
    return Token(type_, lexeme, line, col)


def token_type(t: Token) -> str:
    return t.type


def token_lexeme(t: Token) -> str:
    return t.lexeme


def token_line(t: Token) -> int:
    return t.line


def token_col(t: Token) -> int:
    return t.col


def token_equals(a: Token, b: Token) -> bool:
    return a.type == b.type and a.lexeme == b.lexeme


def token_eof(t: Token) -> bool:
    return t.type == 'eof'


# ----------------------------- errors.aura -----------------------------
@dataclass
class Error:
    kind: str
    line: int
    col: int
    msg: str


def make_error(kind: str, line: int, col: int, msg: str) -> Error:
    return Error(kind, line, col, msg)


def error_kind(e: Error) -> str:
    return e.kind


def error_line(e: Error) -> int:
    return e.line


def error_msg(e: Error) -> str:
    return e.msg


# ----------------------------- stream.aura -----------------------------
@dataclass
class Stream:
    items: List[Any]

    def next(self) -> Any:
        if not self.items:
            return None
        return self.items.pop(0)

    def peek(self) -> Any:
        if not self.items:
            return None
        return self.items[0]

    def eof(self) -> bool:
        return len(self.items) == 0


def stream_from_list(xs: List[Any]) -> Stream:
    return Stream(list(xs))


# ----------------------------- lexer.aura -----------------------------
@dataclass
class Lexer:
    src: str
    pos: int = 0
    line: int = 1
    col: int = 1

    def _peek_ch(self) -> str:
        if self.pos >= len(self.src):
            return ''
        return self.src[self.pos]

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_ws(self) -> None:
        while self.pos < len(self.src) and self.src[self.pos] in ' \t\r\n':
            self._advance()

    def _lex_number(self) -> Token:
        line, col = self.line, self.col
        start = self.pos
        while self.pos < len(self.src) and self.src[self.pos].isdigit():
            self._advance()
        return make_token('num', self.src[start:self.pos], line, col)

    def _lex_ident(self) -> Token:
        line, col = self.line, self.col
        start = self.pos
        while self.pos < len(self.src) and (self.src[self.pos].isalnum() or self.src[self.pos] == '_'):
            self._advance()
        lex = self.src[start:self.pos]
        if lex == 'let':
            return make_token('let', lex, line, col)
        return make_token('id', lex, line, col)

    def next(self) -> Token:
        self._skip_ws()
        if self.pos >= len(self.src):
            return make_token('eof', '', self.line, self.col)
        ch = self._peek_ch()
        if ch.isdigit():
            return self._lex_number()
        if ch.isalpha() or ch == '_':
            return self._lex_ident()
        line, col = self.line, self.col
        if ch in '+-*/();=':
            self._advance()
            return make_token(ch, ch, line, col)
        # Unknown character: skip and return an 'id' of that single char
        # so the parser can surface an unexpected-token error.
        self._advance()
        return make_token('id', ch, line, col)

    def peek(self) -> Token:
        saved_pos, saved_line, saved_col = self.pos, self.line, self.col
        tok = self.next()
        self.pos, self.line, self.col = saved_pos, saved_line, saved_col
        return tok

    def eof(self) -> bool:
        return self.peek().type == 'eof'

    def position(self) -> Tuple[int, int]:
        return (self.line, self.col)


def make_lexer(src: str) -> Lexer:
    return Lexer(src)


# ----------------------------- ast.aura -----------------------------
@dataclass
class ASTNode:
    kind: str
    payload: Tuple = ()


def _node(kind: str, *payload) -> ASTNode:
    return ASTNode(kind, payload)


def make_num(n: int) -> ASTNode:
    return _node('num', n)


def make_var(name: str) -> ASTNode:
    return _node('var', name)


def make_binop(op: str, l: ASTNode, r: ASTNode) -> ASTNode:
    return _node('binop', op, l, r)


def make_let(name: str, val: ASTNode, body: ASTNode) -> ASTNode:
    return _node('let', name, val, body)


def make_seq(exprs: List[ASTNode]) -> ASTNode:
    return _node('seq', list(exprs))


def ast_kind(a: ASTNode) -> str:
    return a.kind


def ast_children(a: ASTNode) -> List[ASTNode]:
    return [c for c in a.payload if isinstance(c, ASTNode)]


def ast_to_list(a: ASTNode) -> list:
    out = [a.kind]
    for p in a.payload:
        if isinstance(p, ASTNode):
            out.append(ast_to_list(p))
        else:
            out.append(p)
    return out


def ast_pretty(a: ASTNode, parent_prec: int = 0) -> str:
    k = a.kind
    if k == 'num':
        return str(a.payload[0])
    if k == 'var':
        return a.payload[0]
    if k == 'binop':
        op, l, r = a.payload
        p = prec_of(op)
        s = ast_pretty(l, p) + ' ' + op + ' ' + ast_pretty(r, p + 1)
        if p < parent_prec:
            s = '(' + s + ')'
        return s
    if k == 'let':
        name, val, body = a.payload
        return 'let ' + name + ' = ' + ast_pretty(val, 0) + '; ' + ast_pretty(body, 0)
    if k == 'seq':
        return '; '.join(ast_pretty(e, 0) for e in a.payload[0])
    return '?'


# ----------------------------- precedence.aura -----------------------------
def prec_of(op: str) -> int:
    if op in ('+', '-'):
        return 1
    if op in ('*', '/'):
        return 2
    return 0


def is_left_assoc(op: str) -> bool:
    return op in ('+', '-', '*', '/')


# ----------------------------- parser.aura -----------------------------
class ParserState:
    def __init__(self, toks: List[Token]):
        self.toks = toks
        self.pos = 0
        self.errors: List[Error] = []
        self.recovered = 0

    def cur(self) -> Token:
        if self.pos < len(self.toks):
            return self.toks[self.pos]
        return self.toks[-1]

    def advance(self) -> Token:
        t = self.cur()
        if self.pos < len(self.toks) - 1:
            self.pos += 1
        return t

    def at(self, type_: str) -> bool:
        return self.cur().type == type_

    def eat(self, type_: str) -> Optional[Token]:
        if self.cur().type == type_:
            t = self.cur()
            self.advance()
            return t
        return None

    def sync(self) -> int:
        n = 0
        while not self.at(';') and not self.at('eof'):
            self.advance()
            n += 1
        if self.at(';'):
            self.advance()
            n += 1
        return n


def parse_program(toks: List[Token]):
    st = ParserState(toks)
    exprs: List[ASTNode] = []
    while not st.at('eof'):
        if st.at(';'):
            st.advance()
            continue
        try:
            exprs.append(parse_expr(st, 0))
        except _ParseFail:
            st.errors.append(_current_error(st))
            n = st.sync()
            st.recovered += n
    if not exprs:
        ast = make_seq([])
    elif len(exprs) == 1:
        ast = exprs[0]
    else:
        ast = make_seq(exprs)
    return ast, st


class _ParseFail(Exception):
    pass


_current_error: List = [None]


def parse_expr(st: ParserState, min_prec: int) -> ASTNode:
    left = parse_primary(st)
    while True:
        tok = st.cur()
        if tok.type not in ('+', '-', '*', '/'):
            break
        p = prec_of(tok.type)
        if p < min_prec:
            break
        op = tok.type
        st.advance()
        right = parse_expr(st, p + 1)
        left = make_binop(op, left, right)
    return left


def parse_primary(st: ParserState) -> ASTNode:
    tok = st.cur()
    if tok.type == 'num':
        st.advance()
        return make_num(int(tok.lexeme))
    if tok.type == 'id':
        st.advance()
        return make_var(tok.lexeme)
    if tok.type == 'let':
        return parse_let(st)
    if tok.type == '(':
        st.advance()
        e = parse_expr(st, 0)
        if not st.eat(')'):
            err = make_error('unexpected-token', st.cur().line, st.cur().col,
                             "expected ')'")
            _current_error[0] = err
            raise _ParseFail()
        return e
    err = make_error('unexpected-token', tok.line, tok.col,
                     "unexpected token '" + tok.lexeme + "'")
    _current_error[0] = err
    raise _ParseFail()


def parse_let(st: ParserState) -> ASTNode:
    st.advance()  # consume 'let'
    name_tok = st.cur()
    if name_tok.type != 'id':
        err = make_error('unexpected-token', name_tok.line, name_tok.col,
                         "expected identifier after let")
        _current_error[0] = err
        raise _ParseFail()
    st.advance()
    if not st.eat('='):
        eq = st.cur()
        err = make_error('unexpected-token', eq.line, eq.col,
                         "expected '='")
        _current_error[0] = err
        raise _ParseFail()
    val = parse_expr(st, 0)
    if not st.eat(';'):
        sc = st.cur()
        err = make_error('unexpected-token', sc.line, sc.col,
                         "expected ';'")
        _current_error[0] = err
        raise _ParseFail()
    body = parse_expr(st, 0)
    return make_let(name_tok.lexeme, val, body)


def parse_errors(st: ParserState) -> List[Error]:
    return st.errors


def recovered_tokens(st: ParserState) -> int:
    return st.recovered


# ----------------------------- tests -----------------------------
TEST_SRC = "let x = 10; x + 2 * (3 - 1)"


def test_lexer():
    lx = make_lexer(TEST_SRC)
    toks = []
    while True:
        t = lx.next()
        toks.append(t)
        if t.type == 'eof':
            break
    last_eof = toks[-1].type == 'eof'
    return len(toks), last_eof, toks


def test_parser_ok():
    n, _, toks = test_lexer()
    ast, st = parse_program(toks)
    return ast, st


def test_parser_errors():
    bad_src = "1 + + 2 ; @ ; 3"
    lx = make_lexer(bad_src)
    toks = []
    while True:
        t = lx.next()
        toks.append(t)
        if t.type == 'eof':
            break
    ast, st = parse_program(toks)
    return st.errors, st.recovered


def count_nodes(a: ASTNode) -> int:
    return 1 + sum(count_nodes(c) for c in ast_children(a))


# ----------------------------- main.aura -----------------------------
def main() -> int:
    # 1) Lex the test source.
    n, last_eof, toks = test_lexer()

    # 2) Parse it.
    ast, st = test_parser_ok()

    # 3) Pretty-print and check round-trip stability.
    pretty = ast_pretty(ast)
    # Re-lex the pretty text and re-parse; the resulting AST must equal the
    # original AST when normalized (here we compare list forms).
    lx2 = make_lexer(pretty)
    toks2 = []
    while True:
        t = lx2.next()
        toks2.append(t)
        if t.type == 'eof':
            break
    ast2, _ = parse_program(toks2)
    stable = ast_to_list(ast) == ast_to_list(ast2)

    # 4) Run error-recovery case.
    errs, recov = test_parser_errors()

    err_count = len(errs)
    err_kind = errs[0].kind if errs else 'none'
    err_line = errs[0].line if errs else 0
    recovered = recov

    # Pretty header (first 60 chars, normalized).
    pretty_head = pretty.replace('\n', ' ')[:60]
    roundtrip_head = ast_pretty(ast2).replace('\n', ' ')[:60]

    lines = [
        f"LEX_TOKENS={n}",
        f"LEX_EOF_OK={'true' if last_eof else 'false'}",
        f"PARSE_OK={'true' if ast else 'false'}",
        f"PARSE_NODES={count_nodes(ast)}",
        f"PRETTY_LEN={len(pretty)}",
        f"ROUNDTRIP_STABLE={'true' if stable else 'false'}",
        f"ERR_COUNT={err_count}",
        f"ERR_KIND={err_kind}",
        f"ERR_LINE={err_line}",
        f"RECOVERED_TOKEN={recovered}",
        f"PRETTY_HEAD={pretty_head}",
        f"ROUNDTRIP_HEAD={roundtrip_head}",
    ]
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
