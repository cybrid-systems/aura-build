# mini-wal-tiered-storage — Tiered WAL with Hot/Cold Archival

A small, in-memory write-ahead log that splits data into a **hot ring buffer** (recent, mutable) and **cold segments** (immutable, sealed, archived). Reads consult a local **readahead cache** that prefetches cold segments. Everything is implemented as plain Aura S-expressions over association lists — no records, no hash tables, no vectors.

The scenario seeds records, forces rotation of the hot buffer into a cold segment, performs cache prefetch + reads, simulates object-store handoff, and verifies that records survive the tiered round-trip with a deterministic byte/record count.

---

## 1. Exact stdout contract

`main.aura` must print exactly these `KEY=value` lines, in this order, one per line, with a trailing newline after each:



15 keys, all required. `WAL_FINAL_LSN=119` is the last appended LSN (`RECORDS_WRITTEN - 1`). `ROUNDTRIP_OK` is `yes` iff every written record (LSN 0..119) reads back with the original payload. `APPEND_LATENCY_OK=yes` iff the simulated append throughput stays above the toy threshold (here: average appends per call ≥ 50).

---

## 2. Module table

All files share one top-level invocation; loaded in order.

| File | Required exported APIs |
|---|---|
| `util.aura` | `(api make-id), (api now-ms), (api fmt-int n), (api acons k v alist), (api alist-ref alist k), (api alist-set! alist k v)` |
| `record.aura` | `(api make-record lsn payload), (api record-lsn r), (api record-payload r), (api record-bytes r)` |
| `hot_ring.aura` | `(api make-hot-ring capacity), (api hot-ring-push! ring lsn payload), (api hot-ring-len ring), (api hot-ring-capacity ring), (api hot-ring-bytes ring), (api hot-ring-snapshot ring)` |
| `cold_segment.aura` | `(api make-cold-segment seg-id), (api cold-segment-add! seg record), (api cold-segment-len seg), (api cold-segment-bytes seg), (api cold-segment-records seg), (api cold-segment-find seg lsn)` |
| `wal.aura` | `(api make-wal capacity records-per-segment), (api wal-append! wal payload), (api wal-len wal), (api wal-read wal lsn), (api wal-lsn-max wal), (api wal-hot-bytes wal), (api wal-sealed-bytes wal), (api wal-segments wal), (api wal-force-rotate! wal), (api wal-roundtrip-ok? wal), (api wal-avg-append-latency wal)` |
| `readahead.aura` | `(api make-readahead max-segments), (api readahead-prefetch! rh seg), (api readahead-lookup rh seg-id), (api readahead-hits rh), (api readahead-misses rh), (api readahead-count rh)` |
| `object_store.aura` | `(api make-object-store name), (api object-store-handoff! os seg), (api object-store-count os), (api object-store-list os)` |
| `local_fs.aura` | `(api make-local-fs name), (api local-fs-handoff! lfs seg), (api local-fs-count lfs), (api local-fs-list lfs)` |
| `cache_metrics.aura` | `(api make-cache-metrics), (api cache-metrics-record-hit! m), (api cache-metrics-record-miss! m), (api cache-metrics-hits m), (api cache-metrics-misses m)` |
| `rotator.aura` | `(api make-rotator), (api rotator-tick! rot wal), (api rotator-seals rot)` |
| `tiered.aura` | `(api make-tiered wal readahead obj-store local-fs metrics), (api tiered-write! t payload), (api tiered-read t lsn), (api tiered-rotate-and-handoff! t), (api tiered-prefetch-segment! t seg), (api tiered-stats t)` |
| `verify.aura` | `(api verify-roundtrip wal), (api verify-append-latency wal threshold), (api verify-summary wal threshold)` |
| `driver.aura` | `(api run-scenario)` — orchestrator; returns an alist of `KEY . value` strings. Does not print. |
| `main.aura` | calls `run-scenario`, then prints each entry as `KEY=value`. No string literals hardcoded as the *values* (only the key names are literals; values come from APIs). |

Total: 14 `.aura` files. `main.aura` is last.

---

## 3. Scenario steps (what `run-scenario` does)

1. Construct `(make-tiered (make-wal 40 40) (make-readahead 4) (make-object-store "obj") (make-local-fs "fs") (make-cache-metrics))`.
2. Loop `tiered-write!` for `i = 0 .. 119`, payload = `fmt-int` of `i` (10-byte representation including length byte, so a record is 16 bytes; 40 records × 16 = 640 bytes? — we treat `record-bytes` as `16` for the LSN+payload envelope; **sealed-bytes = 3 × 2560** is acceptable, but the canonical value printed is whatever the implementation computes consistently; the reference computes `record-bytes = 16`, so sealed = `7680`).
3. After every 40 appends, call `tiered-rotate-and-handoff!`, which: forces the hot ring to flush into a fresh cold segment, hands the segment to the object store (since `OBJECT_STORE_HANDED_OFF=3`), and never to local-fs.
4. After rotation, call `tiered-prefetch-segment!` for the **two most recently sealed segments** (`READAHEAD_PREFETCHED=2`). This populates the readahead cache from the (simulated) object store.
5. Run a deterministic read mix: for `lsn` in `(list 0 5 10 80 90 95 100 119)`, also `tiered-read` 40 random-looking LSNs sampled from cold (drives `COLD_HITS=42` after cache hits; misses on LSNs outside the prefetched segments give `COLD_MISSES=18`). Hot reads (last 40 LSNs) also counted but only cold ones are reported.
6. Force-rotate one more time to drain the hot ring; ensure `HOT_BUFFER_BYTES=0`.
7. Call `(verify-roundtrip wal)` → boolean. Call `(verify-append-latency wal 50)` → boolean. Build `verify-summary` alist.
8. Return the result alist.

`main.aura` walks the alist and prints each entry. The keys printed are exactly the 15 above, in the listed order. The string `yes`/`no` is derived from the boolean via `fmt-int`-free mapping (`if b "yes" "no"`).

---

## 4. Anti-hardcode

`main.aura` contains no `display` call with a hardcoded *value*. Every printed value originates from a function call: `(tiered-stats t)`, `(verify-summary wal 50)`, `(wal-lsn-max wal)`. The only literals in `main.aura` are the key names, the string `"yes"`/`"no"` selector inside a conditional tied to a boolean API result, and `display`/`newline`. Changing `RECORDS_WRITTEN` to 200 in `driver.aura` must propagate to `LSN_MAX`, `WAL_FINAL_LSN`, `SEALED_BYTES`, and `ROUNDTRIP_OK` without touching `main.aura`.

---

## 5. How to run



Expected stdout (15 lines, exact):



---
