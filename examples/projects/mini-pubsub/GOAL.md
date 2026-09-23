# mini-pubsub — 5-file multi-file success predicate

Write a **five-file** Aura program
(`topic.aura` + `sub.aura` + `pub.aura` + `deliver.aura` + `main.aura`) that
implements an in-memory pub/sub bus (topics, subscribers, per-sub mailboxes)
and prints exactly these lines (each plus a trailing newline), **in this order**:

```
SUBS=2
PUB=2
POLL_A=hello
POLL_B=hello
POLL_MISS=miss
AFTER_UNSUB=1
POLL_A2=miss
POLL_B2=world
COUNT=3
```

## Semantics (tick / mailbox model — pure Aura)

Global state after `(bus-init)`:

- **topics**: map name → subscriber-id list
- **mailboxes**: map sub-id → FIFO of pending payloads

| Op | File | Behavior |
|----|------|----------|
| `(bus-init)` | topic.aura | Clear topics + mailboxes |
| `(topic-create name)` | topic.aura | Create topic with empty subscriber list |
| `(subscribe topic sub-id)` | sub.aura | Append `sub-id` to topic's subscribers (idempotent ok); ensure empty mailbox for new sub |
| `(unsubscribe topic sub-id)` | sub.aura | Remove `sub-id` from topic's subscribers (mailbox may remain) |
| `(sub-list topic)` | sub.aura | Return current subscriber-id list (or use length for `SUBS=`) |
| `(publish topic payload)` | pub.aura | Fan-out: append `payload` to **each current** subscriber's mailbox. **Return** delivery count (integer = number of subscribers at publish time). |
| `(poll sub-id)` | deliver.aura | If mailbox empty → `"miss"`. Else pop FIFO head and return payload. |
| `(pending-count sub-id)` | deliver.aura | Length of pending mailbox for `sub-id` |
| `(bus-tick n)` | deliver.aura | Optional; advance a global tick (TTL not required for golden stdout) |

## Scenario (what `main.aura` must do)

1. `(bus-init)`
2. `(topic-create "t")`
3. `(subscribe "t" "a")`, `(subscribe "t" "b")` → print `SUBS=` subscriber count for `"t"` → `2`
4. `(publish "t" "hello")` → fans out to a and b → print `PUB=` delivery count → `2`
5. `(poll "a")` → print `POLL_A=` → `hello`
6. `(poll "b")` → print `POLL_B=` → `hello`
7. `(poll "a")` again → empty → print `POLL_MISS=` → `miss`
8. `(unsubscribe "t" "a")` then `(publish "t" "world")` → print `AFTER_UNSUB=` delivery count → `1` (only b)
9. `(poll "a")` → print `POLL_A2=` → `miss` (unsubscribed; no new delivery)
10. `(poll "b")` → print `POLL_B2=` → `world`
11. `COUNT=` number of the five poll results among
    `{POLL_A, POLL_B, POLL_MISS, POLL_A2, POLL_B2}` that are **not** `miss`
    → `hello`, `hello`, `miss`, `miss`, `world` → **3**

## Required structure (5 files)

- **`topic.aura`** — must define `(define (bus-init) …)` and
  `(define (topic-create name) …)`.
- **`sub.aura`** — must define `(define (subscribe topic sub-id) …)`,
  `(define (unsubscribe topic sub-id) …)`, and `(define (sub-list topic) …)`.
- **`pub.aura`** — must define `(define (publish topic payload) …)`.
- **`deliver.aura`** — must define `(define (poll sub-id) …)` and
  `(define (pending-count sub-id) …)` (optional `(bus-tick n)`).
- **`main.aura`** — must **call** `subscribe` / `publish` / `poll` (and the
  rest of the scenario) — not bare hardcoded display lines alone.

Hardcoding all nine stdout lines in `main.aura` alone without the defines
split across files is a fail.

No Python. Prefer `display` / `newline` / `set!` / `equal?` / lists /
`if` / `let` / `car` / `cdr` / `null?` / `append` / `reverse` / `cond`.

## How multi-file runs under Aura (honest)

```bash
$AURA_BIN topic.aura sub.aura pub.aura deliver.aura main.aura
```

Definitions from earlier files are visible to later ones. This project's
`verify.sh` uses **CLI multi-file** in that order — not a fake module system.

## Why stubs start wrong

`stub/*.aura` are intentionally broken (e.g. publish does not fan-out,
unsubscribe ignored, poll always miss / wrong COUNT) so aura-build's MiniMax
propose → Aura verify → repair loop has real 5-file work.
