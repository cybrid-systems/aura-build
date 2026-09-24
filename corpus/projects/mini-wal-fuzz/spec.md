# mini-wal-fuzz — Crash-safety fuzz harness

A small Append-Only Write-Ahead Log (WAL) exerciser that simulates power-cycles (crashes) at arbitrary points between syscalls (`append`, `sync`, `commit`, `recover`) and then verifies that replay preserves a set of log invariants: monotonic LSN, idempotent recovery, CRC integrity, segment rolling, and tx atomicity. The harness exposes a deterministic fault injector so the fuzz schedule is itself reproducible.

## 1. Overview

The program is split across 11 Aura modules (`.aura` files). Eight of them model the WAL subsystem as pure functions over immutable list snapshots; one owns the seeded RNG / fault scheduler; one is the invariant checker; and the last is `main.aura` which drives a scenario of N rounds and prints `KEY=value` lines summarizing what the harness observed.

All state is held in lists / alists (no record types). "Mutation" is performed by `cons` + `reverse` on shadow copies or by `set!` on top-level mutable globals per module. Crash simulation is modeled as "truncate the recorded journal at a random cut-point" — recovery replays the truncated journal and the checker compares the recovered state to the expected invariants.

## 2. Exact stdout contract

`main.aura` MUST print exactly these lines, in this order, one per line, `KEY=value`, value strings without trailing whitespace, terminated by a final newline:



Values marked `…` are computed by the run; the boolean invariants MUST be `#t` for `VERDICT=PASS`. A single `#f` among the four invariants forces `VERDICT=FAIL`.

## 3. Module table

| File | Required exported API (must exist as a top-level `define`) |
|------|-----------------------------------------------------------|
| `wal_types.aura` | `(api wal-frame? x)`, `(api wal-empty-journal)`, `(api wal-frame-lsn f)`, `(api wal-frame-payload f)`, `(api wal-frame-crc f)`, `(api wal-frame-txid f)`, `(api wal-frame-committed? f)`, `(api wal-frame-set-committed! f v)` |
| `wal_crc.aura` | `(api crc32 bytes)`, `(api crc=? a b)` |
| `wal_segment.aura` | `(api make-segment id cap)`, `(api segment-full? seg)`, `(api segment-append seg frame)`, `(api segment-id seg)`, `(api segment-frames seg)` |
| `wal_log.aura` | `(api log-append log frame)`, `(api log-sync log)`, `(api log-commit log txid)`, `(api log-lsn log)`, `(api log-frames log)`, `(api log-truncate! log n)` |
| `wal_recover.aura` | `(api replay log)`, `(api recover state log)`, `(api recover-idempotent? state log)` |
| `wal_invariants.aura` | `(api check-lsn-monotonic log)`, `(api check-crc-ok log)`, `(api check-tx-atomic state)`, `(api all-invariants state log)` |
| `fuzz_rng.aura` | `(api rng-seed! s)`, `(api rng-next)`, `(api rng-between lo hi)` |
| `fuzz_schedule.aura` | `(api schedule-crash? round)`, `(api schedule-cutpoint frames)`, `(api fault-inject log round)` |
| `harness.aura` | `(api harness-init seed)`, `(api harness-step state round)`, `(api harness-finalize state)` |
| `report.aura` | `(api report-line key value)`, `(api print-report alist)` |
| `main.aura` | `(api run)`, `(api main)` — `main` is the entry point invoked by the CLI |

All modules except `main.aura` MUST be side-effect-light; `main.aura` is the only file that calls `display`/`newline`.

## 4. Scenario steps (executed by `main.aura`)

1. Call `harness-init` with `seed=20260524` and `rounds=120`.
2. Loop `round` from 1 to `rounds`: call `harness-step state round`, which internally:
   a. picks 1–4 `log-append` calls with random payload,
   b. with probability `1/5` calls `log-sync`,
   c. with probability `1/7` calls `log-commit` on a random live txid,
   d. calls `fault-inject`; if a crash is scheduled, the journal is `log-truncate!`'d at `schedule-cutpoint` and `recover` is invoked immediately.
3. After the loop, call `recover` once more on the final state to obtain the canonical recovered state.
4. Run `all-invariants` on `(state, log)`; the four booleans feed the report.
5. Call `harness-finalize` to assemble counters: appended frames, sync calls, commit calls, injected crashes, segment rolls.
6. Call `print-report` with an alist of the 12 `KEY=value` pairs in the exact order above. `print-report` must emit one `KEY=value` line per pair using `display`/`newline`, in the supplied order.

## 5. Anti-hardcode

`main.aura` MUST NOT print literal `PASS` / `#t` / numeric values without first calling the module APIs. Specifically:
- The four `#t`/`#f` invariant values come from `(all-invariants state log)` (returned as a 4-list of booleans), never from a literal.
- `WAL_FUZZ_VERDICT` is computed by `and` across the four booleans and a `> 0` check on `WAL_FUZZ_APPENDED_FRAMES`.
- The five integer counters come from `harness-finalize`, which counts via list lengths of `(log-frames log)` filtered by predicates — not hardcoded constants.
- `WAL_FUZZ_SEED` and `WAL_FUZZ_ROUNDS` are passed in by `main.aura` and must be the same numbers used to seed `rng-seed!` and to bound the `for` loop.

A reviewer can flip `WAL_FUZZ_SEED` in `main.aura` and observe that `APPENDED_FRAMES`, `INJECTED_CRASHES`, `SEGMENT_ROLLS`, and the booleans change accordingly — proving the values flow through the APIs.

## 6. How to run



Expected: exactly 12 `KEY=value` lines on stdout in the order listed in §2, ending with `WAL_FUZZ_VERDICT=PASS`.
