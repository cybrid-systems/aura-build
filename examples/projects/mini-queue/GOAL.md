# mini-queue — 4-file multi-file success predicate

Write a **four-file** Aura program
(`buf.aura` + `lease.aura` + `ops.aura` + `main.aura`) that implements an
in-memory job queue with lease / ack / nack / expire-on-tick, and prints
exactly these lines (each plus a trailing newline), **in this order**:

```
ENQ=2
LEASE_A=j1
LEASE_B=j2
LEASE_MISS=miss
ACK_OK=1
NACK_STATUS=pending
AFTER_TICK=pending
DONE=1
COUNT=4
```

## Semantics (tick / lease model — pure Aura)

Global integer `tick` starts at 0 after `(queue-init)`.

Jobs live in one of: **pending** (FIFO), **leased** (until expire-tick),
**done** (acked).

| Op | Behavior |
|----|----------|
| `(queue-init)` | Clear pending / leased / done; set `tick` to 0 |
| `(queue-enqueue id payload)` | Append job to pending FIFO. **Return** the new pending count (integer). |
| `(queue-lease worker ttl)` | If pending empty → `"miss"`. Else take FIFO head, move to leased with `expire-tick = tick + ttl`, record `worker`, return job `id`. |
| `(queue-tick n)` | `(set! tick (+ tick n))`. Any leased job whose `expire-tick <= tick` returns to **pending** (FIFO append order among expired). |
| `(queue-ack id)` | If `id` is currently leased → remove from leased, mark **done**, return `1`. Else return `0`. |
| `(queue-nack id)` | If `id` is currently leased → move back to **pending**, return `#t` / success. Else no-op. |
| `(queue-status id)` | `"pending"` \| `"leased"` \| `"done"` \| `"missing"` |

## Scenario (what `main.aura` must do)

1. `(queue-init)`
2. `(queue-enqueue "j1" "a")` then `(queue-enqueue "j2" "b")`; print `ENQ=` **pending count** (return value of enqueue / equivalent) → `2`
3. `(queue-lease "w1" 5)` → print `LEASE_A=` id → `j1`
4. `(queue-lease "w1" 5)` → print `LEASE_B=` id → `j2`
5. `(queue-lease "w1" 5)` → print `LEASE_MISS=` → `miss` (nothing pending)
6. `(queue-ack "j1")` → print `ACK_OK=` → `1`
7. `(queue-nack "j2")` then print `NACK_STATUS=` `(queue-status "j2")` → `pending`
8. `(queue-lease "w1" 2)` (takes `j2` again; **do not print**); `(queue-tick 2)` so the lease expires without ack; print `AFTER_TICK=` `(queue-status "j2")` → `pending`
9. `(queue-lease "w1" 5)` then `(queue-ack …)` that job; print `DONE=` ack result → `1`
10. `COUNT=` number of **successful** results among `{LEASE_A, LEASE_B, ACK_OK, DONE}` (job ids or `1`, not `miss`) → `4`

## Required structure (4 files)

- **`buf.aura`** — must define `(define (queue-init) …)` and
  `(define (queue-enqueue id payload) …)`.
- **`lease.aura`** — must define `(define (queue-lease worker ttl) …)` and
  `(define (queue-tick n) …)`.
- **`ops.aura`** — must define `(define (queue-ack id) …)`,
  `(define (queue-nack id) …)`, and `(define (queue-status id) …)`.
- **`main.aura`** — must **call** `queue-init` / `queue-enqueue` / `queue-lease` /
  `queue-tick` / `queue-ack` / `queue-nack` / `queue-status` for the scenario
  (not bare hardcoded display lines alone).

Hardcoding all nine stdout lines in `main.aura` alone without the defines
split across files is a fail.

No Python. Prefer `display` / `newline` / `set!` / `equal?` / lists /
`if` / `let` / `car` / `cdr` / `null?` / `append` / `reverse`.

## How multi-file runs under Aura (honest)

```bash
$AURA_BIN buf.aura lease.aura ops.aura main.aura
```

Definitions from earlier files are visible to later ones. This project's
`verify.sh` uses **CLI multi-file** in that order — not a fake module system.

## Why stubs start wrong

`stub/*.aura` are intentionally broken (e.g. tick does not expire leases,
nack does not return to pending, third lease may lie, COUNT wrong) so
aura-build's MiniMax propose → Aura verify → repair loop has real 4-file work.
