import re

# ---------- token.aura ----------
TOKEN_REGEX = re.compile(r'\s*(?:(\d+\.\d+|\d+)|(\'\')|(\'(?:[^\']|\'\')*\')|(NULL|TRUE|FALSE|AND|OR|NOT|CASE|WHEN|THEN|ELSE|END)|(<=|<>|>=|=|<|>|\+|-|\*|/)|\(|\)|,|[A-Za-z_][A-Za-z0-9_]*)', re.IGNORECASE)

KEYWORDS = {'NULL','TRUE','FALSE','AND','OR','NOT','CASE','WHEN','THEN','ELSE','END'}

def api_tokenize(src):
    tokens = []
    pos = 0
    s = src.strip()
    while pos < len(s):
        m = TOKEN_REGEX.match(s, pos)
        if not m:
            raise ValueError(f"Lex error at: {s[pos:]!r}")
        pos = m.end()
        if m.group(1) is not None:
            tokens.append(('NUM', m.group(1)))
        elif m.group(2) is not None:
            tokens.append(('STR', "''"))
        elif m.group(3) is not None:
            raw = m.group(3)
            inner = raw[1:-1].replace("''", "'")
            tokens.append(('STR', inner))
        elif m.group(4) is not None:
            kw = m.group(4).upper()
            if kw == 'NULL':
                tokens.append(('NULL', 'null'))
            elif kw == 'TRUE':
                tokens.append(('BOOL', 'true'))
            elif kw == 'FALSE':
                tokens.append(('BOOL', 'false'))
            else:
                tokens.append((kw, kw.lower()))
        elif m.group(5) is not None:
            tokens.append(('OP', m.group(5)))
        else:
            tok = m.group(6) or m.group(7) or m.group(8) or m.group(9)
            tokens.append((tok, tok))
    return tokens

def api_token_type(t):
    return t[0]

def api_token_value(t):
    return t[1]

# ---------- ast.aura ----------
def api_make_num(n): return ('num', float(n))
def api_make_str(s): return ('str', s)
def api_make_null(): return ('null',)
def api_make_bool(b): return ('bool', bool(b))
def api_make_var(name): return ('var', name)
def api_make_bin(op, l, r): return ('bin', op, l, r)
def api_make_un(op, e): return ('un', op, e)
def api_make_call(name, args): return ('call', name, args)
def api_make_case(whens, otherwise):
    if otherwise is None:
        otherwise = api_make_null()
    return ('case', whens, otherwise)
def api_make_when(cond, then_v): return ('when', cond, then_v)
def api_ast?(x): return isinstance(x, tuple) and len(x) >= 1

# ---------- env.aura ----------
def api_env_empty():
    return {}

def api_env_set(env, k, v):
    env = dict(env)
    env[k] = v
    return env

def api_env_get(env, k):
    return env.get(k, False)

# ---------- pratt.aura ----------
# Precedence table
PREFIX = {  'OP:+':('r', 70), 'OP:-':('r', 70), 'NOT':('r', 30), 'OP:NEG':('r', 70) }
INFIX  = {  'OP:OR':('l', 10), 'OP:AND':('l', 20), 'OP:=':('l', 40), 'OP:<>':('l', 40),
            'OP:<':('l', 40), 'OP:>':('l', 40), 'OP:<=':('l', 40), 'OP:>=':('l', 40),
            'OP:+':('l', 50), 'OP:-':('l', 50), 'OP:*':('l', 60), 'OP:/':('l', 60) }
def api_prefix_power(sym):
    return PREFIX.get(sym, False)
def api_infix_power(sym):
    return INFIX.get(sym, False)

class Parser:
    def __init__(self, tokens, env):
        self.toks = tokens
        self.i = 0
        self.env = env

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def consume(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def parse(self):
        result = self.expr(0)
        if self.peek()[0] is not None:
            raise ValueError(f"Unexpected token: {self.peek()}")
        return result

    def expr(self, min_p):
        ttype, tval = self.peek()
        if ttype is None:
            raise ValueError("Unexpected end")
        if ttype == 'OP' and ('OP:'+tval) in PREFIX:
            sym = 'OP:'+tval
            assoc, p = PREFIX[sym]
            self.consume()
            r = self.expr(p - 1 if assoc == 'r' else p)
            return api_make_un(tval, r)
        if ttype == 'NOT':
            self.consume()
            assoc, p = PREFIX['NOT']
            r = self.expr(p)  # right assoc for NOT
            return api_make_un('NOT', r)
        if ttype == 'OP' and tval == '-':
            sym = 'OP:-'
            assoc, p = PREFIX[sym]
            self.consume()
            r = self.expr(p)
            return api_make_un('neg', r)
        if ttype == 'OP' and tval == '(':
            self.consume()
            e = self.expr(0)
            if self.peek() != ('OP', ')'):
                raise ValueError("Expected )")
            self.consume()
            return e
        if ttype == 'NUM':
            self.consume()
            n = float(tval) if '.' in tval else int(tval)
            # keep ints as ints, but evaluator will treat them as numeric
            return api_make_num(n)
        if ttype == 'STR':
            self.consume()
            return api_make_str(tval)
        if ttype == 'NULL':
            self.consume()
            return api_make_null()
        if ttype == 'BOOL':
            self.consume()
            return api_make_bool(tval == 'true')
        if ttype == 'CASE':
            return self.parse_case()
        if ttype.isalpha() or ttype.isalnum():
            # could be identifier (var or call)
            name = tval
            self.consume()
            if self.peek() == ('OP', '('):
                self.consume()
                args = []
                if self.peek() != ('OP', ')'):
                    args.append(self.expr(0))
                    while self.peek() == ('OP', ','):
                        self.consume()
                        args.append(self.expr(0))
                if self.peek() != ('OP', ')'):
                    raise ValueError("Expected ) in call")
                self.consume()
                return api_make_call(name, args)
            return api_make_var(name)
        raise ValueError(f"Unexpected token: {ttype} {tval}")

    def parse_case(self):
        self.consume()  # CASE
        whens = []
        while self.peek()[0] == 'WHEN':
            self.consume()
            cond = self.expr(0)
            if self.peek()[0] != 'THEN':
                raise ValueError("Expected THEN")
            self.consume()
            then_v = self.expr(0)
            whens.append(api_make_when(cond, then_v))
        otherwise = None
        if self.peek()[0] == 'ELSE':
            self.consume()
            otherwise = self.expr(0)
        if self.peek()[0] != 'END':
            raise ValueError("Expected END")
        self.consume()
        return api_make_case(whens, otherwise)

def api_parse(tokens, env):
    p = Parser(tokens, env)
    return p.parse()

# ---------- binop / unop / call ----------
def api_apply_bin(op, a, b):
    ta = api_type_of(a)
    tb = api_type_of(b)
    # NULL propagation
    if ta == 'null' or tb == 'null':
        if op == '=':
            return api_make_bool(None if False else (ta == 'null') == (tb == 'null'))
        if op in ('<','>','<=','>=','<>','='):
            return api_make_null()
        return api_make_null()
    # Comparison
    if op == '=':
        return api_make_bool(api_num_of(a) == api_num_of(b) if ta=='num' else a == b)
    if op == '<>':
        return api_make_bool(not (api_num_of(a) == api_num_of(b) if ta=='num' else a == b))
    if op in ('<','>','<=','>='):
        x, y = api_num_of(a), api_num_of(b)
        r = (x < y) if op == '<' else (x > y) if op == '>' else (x <= y) if op == '<=' else (x >= y)
        return api_make_bool(r)
    # Arithmetic / logical
    if op == '+':
        if ta == 'num' and tb == 'num':
            return api_make_num(api_num_of(a) + api_num_of(b))
        if ta == 'str' or tb == 'str':
            return api_make_str(str(a[1] if ta=='str' else a) + str(b[1] if tb=='str' else b))
        return api_make_null()
    if op == '-':
        return api_make_num(api_num_of(a) - api_num_of(b))
    if op == '*':
        return api_make_num(api_num_of(a) * api_num_of(b))
    if op == '/':
        y = api_num_of(b)
        if y == 0:
            return api_make_null()
        return api_make_num(api_num_of(a) / y)
    if op == 'AND':
        return api_make_bool(api_bool_of(a) and api_bool_of(b))
    if op == 'OR':
        return api_make_bool(api_bool_of(a) or api_bool_of(b))
    return api_make_null()

def api_apply_un(op, a):
    if op == 'NOT':
        t = api_type_of(a)
        if t == 'null':
            return api_make_null()
        return api_make_bool(not api_bool_of(a))
    if op == 'neg':
        return api_make_num(-api_num_of(a))
    return a

def api_apply_call(name, args, env):
    # Simple built-ins
    if name.upper() == 'ABS':
        return api_make_num(abs(api_num_of(api_eval_inline(args[0], env))))
    if name.upper() == 'COALESCE':
        for a in args:
            v = api_eval_inline(a, env)
            if api_type_of(v) != 'null':
                return v
        return api_make_null()
    return api_make_null()

# ---------- eval.aura ----------
def api_num_of(v):
    if v[0] == 'num':
        return v[1]
    if v[0] == 'bool':
        return 1 if v[1] else 0
    raise ValueError(f"Not a number: {v}")

def api_bool_of(v):
    if v[0] == 'bool':
        return v[1]
    if v[0] == 'null':
        return False
    if v[0] == 'num':
        return v[1] != 0
    return bool(v[1])

def api_type_of(v):
    return v[0]

def api_eval_inline(node, env):
    if node[0] == 'num' or node[0] == 'str' or node[0] == 'null' or node[0] == 'bool':
        return node
    if node[0] == 'var':
        v = api_env_get(env, node[1])
        if v is False:
            return api_make_null()
        return v
    if node[0] == 'bin':
        op, l, r = node[1], node[2], node[3]
        # short-circuit AND/OR
        if op == 'AND':
            lv = api_eval(l, env)
            if not api_bool_of(lv):
                return api_make_bool(False)
            rv = api_eval(r, env)
            return api_apply_bin(op, lv, rv)
        if op == 'OR':
            lv = api_eval(l, env)
            if api_bool_of(lv):
                return api_make_bool(True)
            rv = api_eval(r, env)
            return api_apply_bin(op, lv, rv)
        return api_apply_bin(op, api_eval(l, env), api_eval(r, env))
    if node[0] == 'un':
        return api_apply_un(node[1], api_eval(node[2], env))
    if node[0] == 'call':
        return api_apply_call(node[1], node[2], env)
    if node[0] == 'case':
        for w in node[1]:
            c = api_eval(w[1], env)
            if api_bool_of(c):
                return api_eval(w[2], env)
        return api_eval(node[2], env)
    return api_make_null()

def api_eval(ast, env):
    return api_eval_inline(ast, env)

# ---------- count nodes ----------
def count_nodes(node):
    if isinstance(node, tuple):
        if node[0] == 'num' or node[0] == 'str' or node[0] == 'null' or node[0] == 'bool' or node[0] == 'var':
            return 1
        if node[0] == 'bin':
            return 1 + count_nodes(node[2]) + count_nodes(node[3])
        if node[0] == 'un':
            return 1 + count_nodes(node[2])
        if node[0] == 'call':
            return 1 + sum(count_nodes(a) for a in node[2])
        if node[0] == 'case':
            n = 1
            for w in node[1]:
                n += count_nodes(w[1]) + count_nodes(w[2])
            if node[2]:
                n += count_nodes(node[2])
            return n
        if node[0] == 'when':
            return count_nodes(node[1]) + count_nodes(node[2])
    return 1

# ---------- repr for typed value ----------
def repr_value(v):
    t = api_type_of(v)
    if t == 'null':
        return 'null'
    if t == 'num':
        n = v[1]
        if isinstance(n, float) and n.is_integer():
            return str(int(n))
        return str(n)
    if t == 'str':
        return repr(v[1])
    if t == 'bool':
        return 'true' if v[1] else 'false'
    return str(v)

def upper_name(tok):
    # Some tokens may already be uppercase keyword strings
    return tok[1].upper()

# ---------- main ----------
def main():
    samples = ["1 + 2 * 3", "-NOT NULL AND (x = NULL)", "CASE WHEN x > 0 THEN x ELSE -x END"]
    env = api_env_set(api_env_empty(), 'x', api_make_num(3))

    lines = []
    lines.append(f"SAMPLES={len(samples)}")
    ok = True
    tokens_lists = []
    asts = []
    for i, expr in enumerate(samples):
        tokens = api_tokenize(expr)
        tokens_lists.append(tokens)
        ast = api_parse(tokens, env)
        asts.append(ast)
        nodes = count_nodes(ast)
        try:
            val = api_eval(ast, env)
        except Exception as e:
            ok = False
            val = ('null',)
        lines.append(f"EXPR[{i}]={expr}")
        lines.append(f"TOKENS[{i}]={len(tokens)}")
        lines.append(f"NODES[{i}]={nodes}")
        lines.append(f"EVAL[{i}]={api_type_of(val)} {repr_value(val)}")
    lines.append(f"RESULT={'PASS' if ok else 'FAIL'}")

    print("\n".join(lines))

if __name__ == '__main__':
    main()
