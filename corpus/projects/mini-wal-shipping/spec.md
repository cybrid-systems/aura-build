```markdown
# mini-wal-shipping — WAL streaming shipper

A small in-memory WAL (Write-Ahead Log) shipper written in Aura. One side
("primary") appends framed pages; the other side ("follower") tails the WAL and
applies frames in order over a framed protocol. Service supports a simple
catch-up handshake, hex-encoded CRC tags, and reconnection stats.

The repository is intentionally mini: no real sockets, no real CRC, no disk.
All state lives in lists/alists in module-local `set!` variables. The point
is to exercise the wiring: append → frame → ship → receive → apply → ack.

---

## 1. Exact stdout contract

After `aura file1.aura … main.aura`, **the very last lines of stdout** must be
the following KEY=value lines, in this exact order, separated by `\n` and
terminated by a single trailing newline:



- `<id>` : 4 hex chars (e.g. `01ab`), generated at runtime, not hardcoded.
- `<n>` : non-negative integers computed from the run.
- `<flag>` : `#t` or `#f`.
- The line ordering and the KEY names are part of the contract.

`expect_keys` (in the same order): `WAL_SHIP_PRIMARY`, `WAL_SHIP_FOLLOWER`,
`WAL_SHIP_PAGES_SHIPPED`, `WAL_SHIP_FRAMES_OK`, `WAL_SHIP_FRAMES_RETRY`,
`WAL_SHIP_BYTES_SHIPPED`, `WAL_SHIP_LSN_HWM`, `WAL_SHIP_CATCHUP_MS`,
`WAL_SHIP_RECONNECTS`, `WAL_SHIP_DROPPED`, `WAL_SHIP_APPLIED_LSN`,
`WAL_SHIP_VERIFIED`.

---

## 2. Module table

All files are `.aura`, loaded in order on one Aura CLI invocation. The last
file is the entry point and is the only file that calls `display`.

| # | File | Required `define (api …)` forms |
|---|------|---------------------------------|
| 1 | `wal_ids.aura`       | `(api ids-random-hex)` `(api ids-make-primary)` `(api ids-make-follower)` |
| 2 | `wal_crc.aura`       | `(api crc-hex-of)` `(api crc-verify?)` |
| 3 | `wal_frame.aura`     | `(api frame-encode)` `(api frame-decode)` `(api frame-flush?)` |
| 4 | `wal_segment.aura`   | `(api seg-append-page)` `(api seg-pages)` `(api seg-lsn-high)` `(api seg-last-flush-lsn)` |
| 5 | `wal_buffer.aura`    | `(api buf-new)` `(api buf-push!)` `(api buf-drain!)` `(api buf-size)` |
| 6 | `wal_sock.aura`      | `(api sock-send!)` `(api sock-recv!) `(api sock-drop?)` `(api sock-reset!)` |
| 7 | `wal_proto.aura`     | `(api proto-handshake)` `(api proto-ship-one!)` `(api proto-recv-loop!)` |
| 8 | `wal_shipper.aura`   | `(api ship-tick!)` `(api ship-stats)` `(api ship-reconnect!)` |
| 9 | `wal_follower.aura`  | `(api follow-attach!)` `(api follow-apply-one!)` `(api follow-applied-lsn)` `(api follow-verify!)` |
|10 | `wal_metrics.aura`   | `(api metrics-record!)` `(api metrics-snapshot)` `(api metrics-render-key)` |
|11 | `wal_reporter.aura`  | `(api report-emit)` |
|12 | `main.aura`         | (entry; orchestrates a full shipping run, then `display`s the contract) |

Notes on individual APIs:

- `ids-random-hex` → `(string)`; returns 4 lowercase hex chars via recursion.
- `ids-make-primary` → `(string)`; `"primary-" ++ (ids-random-hex)`.
- `ids-make-follower` → `(string)`; `"follower-" ++ (ids-random-hex)`.
- `crc-hex-of` → `(string → string)`; deterministic hex over the bytes string.
- `crc-verify?` → `(string string → boolean)`; compares two crc strings.
- `frame-encode` → `(number string string → list)`; `(lsn payload crc)` triplet.
- `frame-decode` → `(list → list)`; returns the same triplet on success, `'()` on a flush marker.
- `frame-flush?` → `(list → boolean)`.
- `seg-append-page` → `(alist string → number)`; returns the new lsn.
- `buf-push!` / `buf-drain!` mutate an alist stored in a module-level `set!`.
- `sock-send!` / `sock-recv!` mutate a shared "transport" alist (simulated socket).
- `proto-ship-one!` / `proto-recv-loop!` use the buffer + socket.
- `ship-tick!` advances one round of shipping, recording metrics.
- `follow-apply-one!` decodes a frame and updates the follower’s applied lsn.
- `report-emit` returns an alist mapping each contract key to its value, ready for `display`.

---

## 3. Scenario steps (executed inside `main.aura`)

`main.aura` performs the following, calling module APIs (never reaching into
their internals), and finishes by printing the 12 contract lines.

1. Call `(ids-make-primary)` and `(ids-make-follower)` to obtain node ids.
2. Build a `wal_segment` via `(seg-append-page seg "hello")` repeated N times
   (N = 7) to produce pages with strictly increasing lsns.
3. Open a simulated transport and call `(proto-handshake primary follower)`.
4. Call `(ship-tick!)` M times (M = 4). For 2 of them, force a drop via
   `(sock-drop?)` then `(ship-reconnect!)`; the others ship cleanly.
5. For each successful tick, call `(follow-apply-one!)` on the follower side
   for every frame in `(buf-drain!)`. Track applied lsn via `(follow-applied-lsn)`.
6. After all ticks, capture stats from `(ship-stats)`, `(follow-applied-lsn)`,
   `(follow-verify?)`, and the metrics snapshot.
7. Compute `(report-emit ...)` and `display` each KEY=value line in order.

Expected contract behavior (values asserted by the grader, not by this file):

- `WAL_SHIP_PAGES_SHIPPED` equals the total number of pages successfully
  transmitted across all ticks (≤ N*M, reduced by drops).
- `WAL_SHIP_FRAMES_RETRY` ≥ 2 (the forced reconnect path).
- `WAL_SHIP_RECONNECTS` ≥ 2.
- `WAL_SHIP_APPLIED_LSN` ≤ `WAL_SHIP_LSN_HWM`.
- `WAL_SHIP_VERIFIED` is `#t` iff every received frame passed `(crc-verify?)`.

---

## 4. Anti-hardcode

`main.aura` **must not** print the expected strings without calling the
module APIs. Concretely:

- The two `"-<id>"` suffixes must come from `ids-random-hex` (visible as
  randomness across runs), not from literal strings in `main.aura`.
- All counters (`PAGES_SHIPPED`, `FRAMES_OK`, `RECONNECTS`, …) must be read
  out of `(ship-stats)` and `(metrics-snapshot)`. Hardcoded integers will
  fail the grader.
- `WAL_SHIP_CATCHUP_MS` must be derived from the actual run length (e.g.
  count of ticks × a per-tick cost constant), not a literal.
- The order of `display` calls is the only allowed order, but the *values*
  printed must come from `report-emit`.

---

## 5. How to run



Any invocation that ends with `main.aura` after the 11 modules in the order
shown above (additional helper files permitted) is acceptable, as long as the
final 12 KEY=value lines match the stdout contract.
json dogfood
{"files":["wal_ids.aura","wal_crc.aura","wal_frame.aura","wal_segment.aura","wal_buffer.aura","wal_sock.aura","wal_proto.aura","wal_shipper.aura","wal_follower.aura","wal_metrics.aura","wal_reporter.aura","main.aura"],"entry":"main.aura","run_mode":"cli_multi","expect_keys":["WAL_SHIP_PRIMARY","WAL_SHIP_FOLLOWER","WAL_SHIP_PAGES_SHIPPED","WAL_SHIP_FRAMES_OK","WAL_SHIP_FRAMES_RETRY","WAL_SHIP_BYTES_SHIPPED","WAL_SHIP_LSN_HWM","WAL_SHIP_CATCHUP_MS","WAL_SHIP_RECONNECTS","WAL_SHIP_DROPPED","WAL_SHIP_APPLIED_LSN","WAL_SHIP_VERIFIED"],"source_res":["\\(define\\s+\\(ids-random-hex\\b","\\(define\\s+\\(ids-make-primary\\b","\\(define\\s+\\(crc-hex-of\\b","\\(define\\s+\\(frame-encode\\b","\\(define\\s+\\(seg-append-page\\b","\\(define\\s+\\(buf-push!\\b","\\(define\\s+\\(sock-send!\\b","\\(define\\s+\\(proto-handshake\\b","\\(define\\s+\\(ship-tick!\\b","\\(define\\s+\\(follow-apply-one!\\b","\\(define\\s+\\(metrics-record!\\b","\\(define\\s+\\(report-emit\\b"]}
```
