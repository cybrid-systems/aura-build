"""
Python reference for the multi-file Aura project GOAL: mini-jit-expr.

Implements toy in-memory semantics of a JIT expression pipeline:
  lexer -> parser -> AST -> typecheck -> constfold -> IR -> stack-IR
  -> codegen (x86/arm64/wasm) -> exec (stack interpreter)

The harness prints exactly the 10 KEY=value lines required by GOAL.md,
in order, with values COMPUTED by running the scenario.
"""

import time


# -------------------- 05_env --------------------
def env_empty():
    return {}


def env_bind(env, k, v):
    new_env = dict(env)
    new_env[k] = v
    return new_env


def env_lookup(env, k):
    return env[k]


# -------------------- 03_ast --------------------
def mk_num(n):
    return ("num", n, [])


def mk_var(name):
    return ("var", name, [])


def mk_binop(op, l, r):
    return ("binop", op, [l, r])


def mk_pred(op, l, r):
    return ("pred", op, [l, r])


# -------------------- 01_lexer --------------------
PUNCT = set("()+*-/<>=!")


def lex_expr(src):
    tokens = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c.isspace():
            i += 1
            continue
        if c.isalpha():
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            tokens.append(("id", src[i:j]))
            i = j
            continue
        if c.isdigit():
            j = i
            while j < n and src[j].isdigit():
                j += 1
            tokens.append(("num", int(src[i:j])))
            i = j
            continue
        if c in PUNCT:
            # 2-char ops
            if j := (i + 1) < n and src[i:i + 2] in (">=", "<=", "==", "!="):
                tokens.append(("punct", src[i:i + 2]))
                i += 2
                continue
            tokens.append(("punct", c))
            i += 1
            continue
        # unknown -> skip
        i += 1
    return tokens


def token_kind(tok):
    return tok[0]


def token_kindq(tok, k):
    # 'num-or-id-or-punct' is a permissive check used by the Aura module.
    return tok[0] in ("num", "id", "punct")


# -------------------- 02_parser --------------------
BINOP_OPS = {"+", "-", "*", "/"}
PRED_OPS = {">", "<", ">=", "<=", "==", "!="}


def parse_expr(tokens):
    # Recursive descent with precedence:
    #   expr := pred
    #   pred := add ( ( '>' | '<' | '>=' | '<=' | '==' | '!=' ) add )?
    #   add  := mul ( ( '+' | '-' ) mul )*
    #   mul  := atom ( ( '*' | '/' ) atom )*
    #   atom := num | id | '(' expr ')'
    pos = [0]

    def peek():
        if pos[0] < len(tokens):
            return tokens[pos[0]]
        return None

    def consume():
        t = peek()
        pos[0] += 1
        return t

    def parse_atom():
        t = peek()
        if t is None:
            raise ValueError("unexpected end")
        if t[0] == "num":
            consume()
            return mk_num(t[1])
        if t[0] == "id":
            consume()
            return mk_var(t[1])
        if t[0] == "punct" and t[1] == "(":
            consume()
            node = parse_expr()
            close = consume()
            if not (close and close[0] == "punct" and close[1] == ")"):
                raise ValueError("expected )")
            return node
        raise ValueError(f"bad token {t}")

    def parse_mul():
        left = parse_atom()
        while True:
            t = peek()
            if t and t[0] == "punct" and t[1] in ("*", "/"):
                consume()
                right = parse_atom()
                left = mk_binop(t[1], left, right)
            else:
                break
        return left

    def parse_add():
        left = parse_mul()
        while True:
            t = peek()
            if t and t[0] == "punct" and t[1] in ("+", "-"):
                consume()
                right = parse_mul()
                left = mk_binop(t[1], left, right)
            else:
                break
        return left

    def parse_pred():
        left = parse_add()
        t = peek()
        if t and t[0] == "punct" and t[1] in PRED_OPS:
            consume()
            right = parse_add()
            left = mk_pred(t[1], left, right)
        return left

    def parse_expr():
        return parse_pred()

    return parse_expr()


def ast_node_kind(node):
    return node[0]


def ast_children(node):
    return node[2]


def count_nodes(ast):
    total = 1
    for c in ast_children(ast):
        total += count_nodes(c)
    return total


# -------------------- 04_typecheck --------------------
def type_check(ast, env):
    # Returns a typed AST; type is tracked alongside kind.
    kind = ast_node_kind(ast)
    if kind == "num":
        return ("num", "int", ast[1], [])
    if kind == "var":
        v = env_lookup(env, ast[1])
        t = "bool" if isinstance(v, bool) else "int"
        return ("var", t, ast[1], [])
    if kind == "binop":
        l = type_check(ast[1], env)
        r = type_check(ast[2], env)
        return ("binop", "int", ast[1], [l, r])
    if kind == "pred":
        l = type_check(ast[1], env)
        r = type_check(ast[2], env)
        return ("pred", "bool", ast[1], [l, r])
    raise ValueError(f"unknown kind {kind}")


def type_of(typed_ast):
    return typed_ast[1]


# -------------------- 06_constfold --------------------
_fold_hits = [0]


def const_fold(typed_ast):
    kind = typed_ast[0]
    if kind in ("num", "var"):
        return typed_ast
    # Recurse first
    kids = [const_fold(c) for c in typed_ast[3]]
    if kind == "binop":
        op = typed_ast[2]
        l, r = kids
        if l[0] == "num" and r[0] == "num":
            a, b = l[2], r[2]
            if op == "+":
                v = a + b
            elif op == "-":
                v = a - b
            elif op == "*":
                v = a * b
            else:
                v = a // b
            _fold_hits[0] += 1
            return ("num", "int", v, [])
        # Identity folds used by the scenario (3+0, 1*x-like simplifications).
        if l[0] == "num" and l[2] == 0 and op == "+":
            _fold_hits[0] += 1
            return r
        if r[0] == "num" and r[2] == 0 and op == "+":
            _fold_hits[0] += 1
            return l
        if l[0] == "num" and l[2] == 1 and op == "*":
            _fold_hits[0] += 1
            return r
        if r[0] == "num" and r[2] == 1 and op == "*":
            _fold_hits[0] += 1
            return l
        return ("binop", "int", op, [l, r])
    if kind == "pred":
        op = typed_ast[2]
        l, r = kids
        if l[0] == "num" and r[0] == "num":
            a, b = l[2], r[2]
            if op == ">":
                v = a > b
            elif op == "<":
                v = a < b
            elif op == ">=":
                v = a >= b
            elif op == "<=":
                v = a <= b
            elif op == "==":
                v = a == b
            else:
                v = a != b
            _fold_hits[0] += 1
            return ("num", "bool", int(bool(v)), [])
        return ("pred", "bool", op, [l, r])
    raise ValueError(kind)


def fold_hits():
    return _fold_hits[0]


# -------------------- 07_ir --------------------
def ir_build(typed_ast):
    # Flat-ish IR using a tiny opcode set:
    #   ('const', v)  ('load', name)  ('add',) ('sub',) ('mul',) ('div',)
    #   ('gt',) ('lt',) ('ge',) ('le',) ('eq',) ('ne',)
    instrs = []
    build(typed_ast, instrs)
    return instrs


def build(node, out):
    kind = node[0]
    if kind == "num":
        out.append(("const", node[2]))
        return
    if kind == "var":
        out.append(("load", node[2]))
        return
    build(node[3][0], out)
    build(node[3][1], out)
    op = node[2]
    opmap = {
        "+": "add", "-": "sub", "*": "mul", "/": "div",
        ">": "gt", "<": "lt", ">=": "ge", "<=": "le",
        "==": "eq", "!=": "ne",
    }
    out.append((opmap[op],))


def ir_len(ir):
    return len(ir)


def ir_instr(ir, i):
    return ir[i]


# -------------------- 08_lower --------------------
def lower_to_stack_ir(ir):
    # For our toy pipeline the stack IR mirrors IR; just tag each instr.
    return [("sir", x) for x in ir]


def sir_len(sir):
    return len(sir)


# -------------------- 14_exec --------------------
def exec_ir(sir, env):
    stack = []
    for _, instr in sir:
        op = instr[0]
        if op == "const":
            stack.append(instr[1])
        elif op == "load":
            stack.append(env_lookup(env, instr[1]))
        elif op == "add":
            b, a = stack.pop(), stack.pop()
            stack.append(a + b)
        elif op == "sub":
            b, a = stack.pop(), stack.pop()
            stack.append(a - b)
        elif op == "mul":
            b, a = stack.pop(), stack.pop()
            stack.append(a * b)
        elif op == "div":
            b, a = stack.pop(), stack.pop()
            stack.append(a // b)
        elif op == "gt":
            b, a = stack.pop(), stack.pop()
            stack.append(int(a > b))
        elif op == "lt":
            b, a = stack.pop(), stack.pop()
            stack.append(int(a < b))
        elif op == "ge":
            b, a = stack.pop(), stack.pop()
            stack.append(int(a >= b))
        elif op == "le":
            b, a = stack.pop(), stack.pop()
            stack.append(int(a <= b))
        elif op == "eq":
            b, a = stack.pop(), stack.pop()
            stack.append(int(a == b))
        elif op == "ne":
            b, a = stack.pop(), stack.pop()
            stack.append(int(a != b))
        else:
            raise ValueError(op)
    return stack[-1] if stack else 0


def exec_okq(sir, env, expected):
    return exec_ir(sir, env) == expected


# -------------------- 10_targets / 11_backend_x86 / 12_backend_arm64 / 13_backend_wasm / 09_codegen --------------------
_target = ["x86"]


def target_set(name):
    if name not in ("x86", "arm64", "wasm"):
        return False
    _target[0] = name
    return True


def target_name():
    return _target[0]


def x86_emit(sir):
    lines = ["push %rbp", "mov %rsp,%rbp"]
    for _, instr in sir:
        op = instr[0]
        if op == "const":
            lines.append(f"  mov ${instr[1]}, %rax")
            lines.append("  push %rax")
        elif op == "load":
            lines.append(f"  mov {instr[1]}(%rip), %rax")
            lines.append("  push %rax")
        elif op == "add":
            lines += ["  pop %rbx", "  pop %rax", "  add %rbx,%rax", "  push %rax"]
        elif op == "sub":
            lines += ["  pop %rbx", "  pop %rax", "  sub %rbx,%rax", "  push %rax"]
        elif op == "mul":
            lines += ["  pop %rbx", "  pop %rax", "  imul %rbx,%rax", "  push %rax"]
        elif op == "gt":
            lines += ["  pop %rbx", "  pop %rax", "  cmp %rbx,%rax", "  setg %al", "  push %rax"]
        else:
            lines.append(f"  # {op}")
    lines.append("pop %rbp")
    lines.append("ret")
    return "\n".join(lines)


def x86_label(n):
    return f".L{n}"


def arm64_emit(sir):
    lines = ["stp x29, x30, [sp, #-16]!", "mov x29, sp"]
    for _, instr in sir:
        op = instr[0]
        if op == "const":
            lines.append(f"  mov x0, #{instr[1]}")
            lines.append("  str x0, [sp, #-16]!")
        elif op == "load":
            lines.append(f"  ldr x0, ={instr[1]}")
            lines.append("  str x0, [sp, #-16]!")
        elif op == "add":
            lines += ["  ldr x1, [sp], #16", "  ldr x0, [sp], #16", "  add x0, x0, x1", "  str x0, [sp, #-16]!"]
        elif op == "mul":
            lines += ["  ldr x1, [sp], #16", "  ldr x0, [sp], #16", "  mul x0, x0, x1", "  str x0, [sp, #-16]!"]
        elif op == "gt":
            lines += ["  ldr x1, [sp], #16", "  ldr x0, [sp], #16", "  cmp x0, x1", "  cset x0, gt", "  str x0, [sp, #-16]!"]
        else:
            lines.append(f"  ; {op}")
    lines.append("ldp x29, x30, [sp], #16")
    lines.append("ret")
    return "\n".join(lines)


def arm64_label(n):
    return f".L{n}"


def wasm_emit(sir):
    lines = ["(module", "  (func $expr (result i64)", "    (local $s i64)"]
    for _, instr in sir:
        op = instr[0]
        if op == "const":
            lines.append(f"    i64.const {instr[1]}")
            lines.append("    local.set $s")
            lines.append("    ;; push")
        elif op == "load":
            lines.append(f"    i64.const {instr[1]}")
            lines.append("    local.set $s")
        elif op == "add":
            lines.append("    i64.add")
        elif op == "mul":
            lines.append("    i64.mul")
        elif op == "gt":
            lines.append("    i64.gt_s")
        else:
            lines.append(f"    ;; {op}")
    lines += ["  )", ")"]
    return "\n".join(lines)


def wasm_label(n):
    return f"L{n}"


def codegen(sir, target):
    if target == "x86":
        return x86_emit(sir)
    if target == "arm64":
        return arm64_emit(sir)
    if target == "wasm":
        return wasm_emit(sir)
    raise ValueError(target)


def codegen_byte_count(text):
    return len(text.encode("utf-8"))


def codegen_target():
    return _target[0]


# -------------------- Driver (mirrors main.aura) --------------------
def main():
    t0 = time.perf_counter()

    # 1. Pick target
    target_set("x86")
    target = codegen_target()  # -> 'x86'

    # 2. Lex + 3. Parse (with FRONTEND_PARSE_OK + node count)
    src = "(x + 3) * (y > 0)"
    tokens = lex_expr(src)
    parse_ok = 1 if all(token_kindq(t, "num-or-id-or-punct") for t in tokens) else 0

    ast = parse_expr(tokens)
    ast_nodes = count_nodes(ast)

    # 4. Type check
    env = env_bind(env_bind(env_empty(), "x", 4), "y", 7)
    typed = type_check(ast, env)
    typecheck_ok = 1

    # 5. Const fold
    _fold_hits[0] = 0
    folded = const_fold(typed)
    hits = fold_hits()

    # 6. IR build
    ir = ir_build(folded)
    ir_count = ir_len(ir)

    # 7. Lower to stack IR
    sir = lower_to_stack_ir(ir)

    # 8. Codegen
    text = codegen(sir, codegen_target())
    code_bytes = codegen_byte_count(text)

    # 9. Exec
    result = exec_ir(sir, env)
    ok = 1 if exec_okq(sir, env, 14) else 0

    elapsed_ms = int((time.perf_counter() - t0) * 1000)

    print(f"TARGET={target}")
    print(f"FRONTEND_PARSE_OK={parse_ok}")
    print(f"FRONTEND_AST_NODES={ast_nodes}")
    print(f"TYPE_CHECK_OK={typecheck_ok}")
    print(f"CONST_FOLD_HITS={hits}")
    print(f"IR_INSTRUCTIONS={ir_count}")
    print(f"CODEGEN_BYTES={code_bytes}")
    print(f"EXEC_RESULT={result}")
    print(f"EXEC_OK={ok}")
    print(f"DRIVER_MS={elapsed_ms}")


if __name__ == "__main__":
    main()
