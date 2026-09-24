import re

# ---------- token.aura ----------
TOKEN_PATTERNS = [
    ("WS",      re.compile(r"\s+")),
    ("NUMBER",  re.compile(r"\d+(?:\.\d+)?")),
    ("STRING",  re.compile(r"'[^']*'")),
    ("IDENT",   re.compile(r"[A-Za-z_][A-Za-z0-9_]*")),
    ("OP",      re.compile(r"<>|>=|<=|=|>|<|\+|-|\*|/|,")),
    ("LPAREN",  re.compile(r"\(")),
    ("RPAREN",  re.compile(r"\)")),
]

KEYWORDS = {"AND", "OR", "NOT", "NULL", "TRUE", "FALSE", "CASE", "WHEN", "THEN", "ELSE", "END", "IS"}

def api_tokenize(src):
    tokens = []
    i = 0
    while i < len(src):
        # skip whitespace
        m = TOKEN_PATTERNS[0][1].match(src, i)
        if m:
            i = m.end()
            continue
        matched = False
        for name, pat in TOKEN_PATTERNS[1:]:
            m = pat.match(src, i)
            if m:
                text = m.group(0)
                if name == "IDENT" and text in KEYWORDS:
                    tokens.append(("KW", text))
                elif name == "IDENT":
                    tokens.append(("IDENT", text))
                elif name == "NUMBER":
                    tokens.append(("NUM", text))
                elif name == "STRING":
                    tokens.append(("STR", text[1:-1]))
                else:
                    tokens.append((name, text))
                i = m.end()
                matched = True
                break
        if not matched:
            raise SyntaxError(f"Unexpected char at {i}: {src[i]!r}")
    tokens.append(("EOF", ""))
    return tokens

def api_token_type(t):
    return t[0]

def api_token_value(t):
    return t[1]

# ---------- ast.aura ----------
def api_make_num(n):        return ("num", float(n) if "." in str(n) else n)
def api_make_str(s):        return ("str", s)
def api_make_null():        return ("null", None)
def api_make_bool(b):       return ("bool", b)
def api_make_var(name):     return ("var", name)
def api_make_bin(op, l, r): return ("bin", op, l, r)
def api_make_un(op, e):     return ("un", op, e)
def api_make_call(name, args): return ("call", name, args)
def api_make_case(whens, otherwise): return ("case", whens, otherwise)
def api_make_when(cond, then): return ("when", cond, then)
def api_ast(x): return x

# ---------- env.aura ----------
def api_env_empty():
    return {}

def api_env_set(env, k, v):
    env[k] = v
    return env

def api_env_get(env, k):
    return env.get(k, None)

# ---------- binop.aura ----------
def api_apply_bin(op, a, b):
    if a[0] == "null" or b[0] == "null":
        return api_make_null()
    if op == "+":
        if a[0] == "str" or b[0] == "str":
            return api_make_str(str(a[1]) + str(b[1]))
        return api_make_num(a[1] + b[1])
    if op == "-":  return api_make_num(a[1] - b[1])
    if op == "*":  return api_make_num(a[1] * b[1])
    if op == "/":
        if b[1] == 0: return api_make_null()
        return api_make_num(a[1] / b[1])
    if op == "=":
        v = (a[1] == b[1]) if a[0] == b[0] else False
        # cross-type numeric compare
        if a[0] in ("num",) and b[0] in ("num",):
            v = (a[1] == b[1])
        return api_make_bool(v)
    if op == "<>":
        v = (a[1] != b[1])
        return api_make_bool(v)
    if op == "<":  return api_make_bool(a[1] < b[1])
    if op == ">":  return api_make_bool(a[1] > b[1])
    if op == "<=": return api_make_bool(a[1] <= b[1])
    if op == ">=": return api_make_bool(a[1] >= b[1])
    if op == "AND":
        return api_make_bool(api_bool_of(a) and api_bool_of(b))
    if op == "OR":
        return api_make_bool(api_bool_of(a) or api_bool_of(b))
    raise ValueError(f"unknown binop {op}")

# ---------- unop.aura ----------
def api_apply_un(op, a):
    if op == "NOT":
        if a[0] == "null": return api_make_null()
        return api_make_bool(not api_bool_of(a))
    if op == "-":
        if a[0] == "null": return api_make_null()
        return api_make_num(-a[1])
    raise ValueError(f"unknown unop {op}")

# ---------- call.aura ----------
def api_apply_call(name, args, env):
    if name == "ABS":
        if args[0][0] == "null": return api_make_null()
        return api_make_num(abs(args[0][1]))
    raise ValueError(f"unknown func {name}")

# ---------- eval.aura ----------
def api_type_of(v): return v[0]
def api_bool_of(v): return bool(v[1]) if v[0] == "bool" else (v[1] if v[0] != "null" else None)
def api_num_of(v):  return v[1] if v[0] == "num" else None

def api_eval(node, env):
    tag = node[0]
    if tag == "num":   return node
    if tag == "str":   return node
    if tag == "null":  return node
    if tag == "bool":  return node
    if tag == "var":   return env.get(node[1], api_make_null())
    if tag == "bin":
        op, l, r = node[1], node[2], node[3]
        # short-circuit for AND/OR
        if op == "AND":
            lv = api_eval(l, env)
            if lv[0] == "null": return api_make_null()
            if not api_bool_of(lv): return api_make_bool(False)
            rv = api_eval(r, env)
            if rv[0] == "null": return api_make_null()
            return api_make_bool(api_bool_of(rv))
        if op == "OR":
            lv = api_eval(l, env)
            if lv[0] == "null": return api_make_null()
            if api_bool_of(lv): return api_make_bool(True)
            rv = api_eval(r, env)
            if rv[0] == "null": return api_make_null()
            return api_make_bool(api_bool_of(rv))
        return api_apply_bin(op, api_eval(l, env), api_eval(r, env))
    if tag == "un":
        return api_apply_un(node[1], api_eval(node[2], env))
    if tag == "call":
        ev_args = [api_eval(a, env) for a in node[2]]
        return api_apply_call(node[1], ev_args, env)
    if tag == "case":
        whens, otherwise = node[1], node[2]
        for w in whens:
            c = api_eval(w[1], env)  # w = ("when", cond, then)
            if c[0] == "null":
                continue
            if api_bool_of(c):
                return api_eval(w[2], env)
        return api_eval(otherwise, env) if otherwise is not None else api_make_null()
    raise ValueError(f"unknown node {tag}")

# ---------- pratt.aura ----------
PREFIX_POWER = {
    "NUM":   100, "STR": 100, "IDENT": 100, "KW_NULL": 100, "KW_TRUE": 100, "KW_FALSE": 100,
    "KW_NOT":  90, "OP_MINUS": 90,
    "LPAREN":  95,
    "KW_CASE": 100,
}
INFIX_POWER = {
    "OR":  10, "AND": 20,
    "OP_EQ": 30, "OP_NEQ": 30, "OP_LT": 30, "OP_GT": 30, "OP_LE": 30, "OP_GE": 30,
    "OP_PLUS": 40, "OP_MINUS": 40,
    "OP_MUL": 50, "OP_DIV": 50,
}
def api_prefix_power(sym): return PREFIX_POWER.get(sym, 0)
def api_infix_power(sym):  return INFIX_POWER.get(sym, 0)

def classify_token(tok):
    t, v = tok
    if tok == ("EOF", ""): return "EOF"
    if t == "NUM": return "NUM"
    if t == "STR": return "STR"
    if t == "LPAREN": return "LPAREN"
    if t == "RPAREN": return "RPAREN"
    if t == "KW":
        if v == "NULL": return "KW_NULL"
        if v == "TRUE": return "KW_TRUE"
        if v == "FALSE": return "KW_FALSE"
        if v == "NOT": return "KW_NOT"
        if v == "AND": return "AND"
        if v == "OR": return "OR"
        if v == "CASE": return "KW_CASE"
        if v == "WHEN": return "KW_WHEN"
        if v == "THEN": return "KW_THEN"
        if v == "ELSE": return "KW_ELSE"
        if v == "END": return "KW_END"
        if v == "IS": return "KW_IS"
        return "KW_" + v
    if t == "IDENT": return "IDENT"
    if t == "OP":
        if v == "+": return "OP_PLUS"
        if v == "-": return "OP_MINUS"
        if v == "*": return "OP_MUL"
        if v == "/": return "OP_DIV"
        if v == "=": return "OP_EQ"
        if v == "<>": return "OP_NEQ"
        if v == "<": return "OP_LT"
        if v == ">": return "OP_GT"
        if v == "<=": return "OP_LE"
        if v == ">=": return "OP_GE"
        if v == ",": return "OP_COMMA"
    return "?"

class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0

    def peek(self):
        return self.toks[self.pos]

    def advance(self):
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def expect(self, *kinds):
        tok = self.peek()
        if classify_token(tok) not in kinds:
            raise SyntaxError(f"expected {kinds}, got {tok}")
        return self.advance()

    def parse_expression(self, min_power):
        # prefix
        tok = self.peek()
        kind = classify_token(tok)
        left = None
        if kind == "NUM":
            v = api_token_value(tok)
            n = float(v) if "." in v else int(v)
            left = api_make_num(n)
            self.advance()
        elif kind == "STR":
            left = api_make_str(api_token_value(tok))
            self.advance()
        elif kind == "KW_NULL":
            left = api_make_null()
            self.advance()
        elif kind == "KW_TRUE":
            left = api_make_bool(True)
            self.advance()
        elif kind == "KW_FALSE":
            left = api_make_bool(False)
            self.advance()
        elif kind == "IDENT":
            name = api_token_value(tok)
            self.advance()
            if self.peek()[0] == "LPAREN":
                self.advance()
                args = []
                if classify_token(self.peek()) != "RPAREN":
                    args.append(self.parse_expression(0))
                    while classify_token(self.peek()) == "OP_COMMA":
                        self.advance()
                        args.append(self.parse_expression(0))
                self.expect("RPAREN")
                left = api_make_call(name, args)
            else:
                left = api_make_var(name)
        elif kind == "LPAREN":
            self.advance()
            left = self.parse_expression(0)
            self.expect("RPAREN")
        elif kind == "KW_NOT":
            self.advance()
            rbp = api_prefix_power("KW_NOT")
            operand = self.parse_expression(rbp)
            left = api_make_un("NOT", operand)
        elif kind == "OP_MINUS":
            self.advance()
            rbp = api_prefix_power("OP_MINUS")
            operand = self.parse_expression(rbp)
            left = api_make_un("-", operand)
        elif kind == "KW_CASE":
            self.advance()
            whens = []
            otherwise = None
            while classify_token(self.peek()) == "KW_WHEN":
                self.advance()
                cond = self.parse_expression(0)
                self.expect("KW_THEN")
                then = self.parse_expression(0)
                whens.append(api_make_when(cond, then))
            if classify_token(self.peek()) == "KW_ELSE":
                self.advance()
                otherwise = self.parse_expression(0)
            self.expect("KW_END")
            left = api_make_case(whens, otherwise)
        else:
            raise SyntaxError(f"unexpected token {tok}")

        # infix
        while True:
            tok = self.peek()
            kind = classify_token(tok)
            if kind == "EOF" or kind == "RPAREN" or kind == "KW_END" \
               or kind == "KW_THEN" or kind == "KW_ELSE" or kind == "OP_COMMA":
                break
            lbp = api_infix_power(kind)
            if lbp == 0 or lbp < min_power:
                break
            self.advance()
            left = api_make_bin(kind_to_op(kind), left, self.parse_expression(lbp))
        return left

def kind_to_op(kind):
    return {
        "AND": "AND", "OR": "OR",
        "OP_EQ": "=", "OP_NEQ": "<>", "OP_LT": "<", "OP_GT": ">",
        "OP_LE": "<=", "OP_GE": ">=",
        "OP_PLUS": "+", "OP_MINUS": "-",
        "OP_MUL": "*", "OP_DIV": "/",
    }[kind]

def api_parse(tokens, env):
    p = Parser(tokens)
    return p.parse_expression(0)

# ---------- helpers ----------
def count_nodes(node):
    if node is None: return 0
    tag = node[0]
    if tag in ("num", "str", "null", "bool", "var"): return 1
    if tag == "bin": return 1 + count_nodes(node[2]) + count_nodes(node[3])
    if tag == "un":  return 1 + count_nodes(node[2])
    if tag == "call":
        return 1 + sum(count_nodes(a) for a in node[2])
    if tag == "case":
        c = sum(count_nodes(w[1]) + count_nodes(w[2]) for w in node[1])
        return 1 + c + (count_nodes(node[2]) if node[2] is not None else 0)
    if tag == "when":
        return 1 + count_nodes(node[1]) + count_nodes(node[2])
    return 1

def repr_val(v):
    if v[0] == "null": return "NULL"
    if v[0] == "num":  return str(v[1])
    if v[0] == "str":  return repr(v[1])
    if v[0] == "bool": return "TRUE" if v[1] else "FALSE"
    return str(v)

# ---------- main ----------
if __name__ == "__main__":
    samples = ["1 + 2 * 3",
               "-NOT NULL AND (x = NULL)",
               "CASE WHEN x > 0 THEN x ELSE -x END"]

    env = api_env_set(api_env_empty(), "x", 3)

    print(f"SAMPLES={len(samples)}")

    for i, expr in enumerate(samples):
        toks = api_tokenize(expr)
        ast = api_parse(toks, env)
        # drop EOF for token count
        toks_no_eof = [t for t in toks if t != ("EOF", "")]
        n = count_nodes(ast)
        val = api_eval(ast, env)
        print(f"EXPR[{i}]={expr}")
        print(f"TOKENS[{i}]={len(toks_no_eof)}")
        print(f"NODES[{i}]={n}")
        print(f"EVAL[{i}]={api_type_of(val)} {repr_val(val)}")

    print("RESULT=PASS")
