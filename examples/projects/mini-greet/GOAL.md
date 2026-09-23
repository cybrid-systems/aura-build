# mini-greet — success predicate

Write a small **Aura** program that prints exactly this line (plus a trailing newline):

```
GREET=aura
```

## Exact stdout contract

- A line matching `GREET=aura` must appear in stdout when run with `$AURA_BIN`.
- No Python. Prefer `(display "GREET=aura")(newline)`.
- `verify.sh` exits 0 iff that exact token is present and Aura did not report an error.

## Why stub starts wrong

`stub.aura` intentionally prints the wrong greeting so aura-build’s
MiniMax propose → Aura verify → repair loop has real work (see
`aura-build llm-dogfood --task greet`).
