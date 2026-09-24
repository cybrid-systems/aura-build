# WAL Compaction Daemon — mini-wal-compactor

A toy in-memory **WAL (write-ahead log) compaction daemon** that periodically scans a simulated on-disk log, merges cold segments into compacted snapshots, drops tombstone-marked entries, and emits summary statistics. All state lives in list/alist structures manipulated via small per-module APIs. The main file orchestrates one compaction cycle and prints a strict `KEY=value` stdout contract.

---

## 1. Exact stdout contract

The scenario (run via `aura file1.aura ... main.aura`) MUST print these lines **in this exact order**, each terminated by a newline. `KEY` is uppercase, `value` is computed at runtime by calling module APIs (never hard-coded).



13 keys, deterministic order. The reference (Python) run measures each value from actual API output — never from the GOAL.md.

---

## 2. Module table

Each file is loaded in order on a single Aura CLI invocation (shared top-level). The last file is the entry point.

| # | File | Required `(define (api …))` forms |
|---|------|-----------------------------------|
| 1 | `wal_segment.aura` | `(api make-segment id age entries)`, `(api segment-id seg)`, `(api segment-age seg)`, `(api segment-entries seg)`, `(api segment-byte-size seg)`, `(api segment-tombstone? seg)` |
| 2 | `wal_entry.aura` | `(api make-entry key value op)`, `(api entry-key e)`, `(api entry-value e)`, `(api entry-op e)`, `(api entry-tombstone? e)` |
| 3 | `wal_log.aura` | `(api make-log)`, `(api log-append log seg)`, `(api log-all-segments log)`, `(api log-size-bytes log)`, `(api log-entry-count log)`, `(api log-cold-segments log threshold)`, `(api log-drop-segment log id)` |
| 4 | `cold_detector.aura` | `(api classify-cold segments threshold)`, `(api cold-count cold-list)`, `(api cold-ids cold-list)` |
| 5 | `merger.aura` | `(api merge-segments cold-list)`, `(api merged-entries merged)`, `(api merged-byte-size merged)`, `(api merged-source-ids merged)` |
| 6 | `tombstone_sweeper.aura` | `(api sweep-tombstones entries)`, `(api sweep-stats sweeper)`, `(api sweep-kept sweeper)`, `(api sweep-dropped sweeper)` |
| 7 | `snapshot_writer.aura` | `(api write-snapshot merged id)`, `(api snapshot-id snap)`, `(api snapshot-entries snap)`, `(api snapshot-byte-size snap)` |
| 8 | `byte_counter.aura` | `(api total-bytes items)`, `(api diff-bytes before after)`, `(api compression-ratio before after)` |
| 9 | `cycle_counter.aura` | `(api make-cycle-counter)`, `(api cycle-tick cc)`, `(api cycle-count cc)` |
| 10 | `stats_collector.aura` | `(api make-stats)`, `(api stat-inc! stats key n)`, `(api stat-get stats key)`, `(api stat-all stats)`, `(api stats->alist stats)` |
| 11 | `summary_printer.aura` | `(api format-key-value key value)`, `(api format-ratio value)`, `(api print-summary alist)` |
| 12 | `daemon_state.aura` | `(api make-daemon)`, `(api daemon-status daemon)`, `(api daemon-set-status! daemon status)`, `(api daemon-run-cycle! daemon)`, `(api daemon-cycles daemon)` |
| 13 | `main.aura` | entry point — orchestrates one full cycle, calls module APIs, prints contract |

---

## 3. Scenario steps (executed in `main.aura`)

The entry point runs **one** compaction cycle end-to-end. Each step calls the listed APIs (no string literals like `"42"` may appear as a value source for the contract keys):

1. **Build the log** via `wal_log` + `wal_segment` + `wal_entry`:
   - Append 5 segments: 3 cold (age ≥ threshold) and 2 hot (age < threshold).
   - Cold segments contain a mix of live entries and tombstone entries.
   - One cold segment is entirely tombstones (eligible for full drop).
2. **Count segments scanned** via `log-all-segments` length.
3. **Classify cold segments** via `cold_detector/classify-cold` using `COLD_THRESHOLD=3`.
4. **Merge cold segments** via `merger/merge-segments` → produces one merged segment payload (entries list + source ids).
5. **Sweep tombstones** via `tombstone_sweeper/sweep-tombstones` on merged entries.
6. **Emit snapshots** via `snapshot_writer/write-snapshot` — one snapshot per merged payload; dropped segments are not snapshotted.
7. **Drop fully-consumed cold segments** from the log via `log-drop-segment`.
8. **Compute byte stats** via `byte_counter/total-bytes` (before) and post-compaction log size (after), plus `compression-ratio`.
9. **Increment cycle counter** via `cycle_counter/cycle-tick`.
10. **Collect stats** via `stats_collector` for `SEGMENTS_MERGED`, `TOMBSTONES_DROPPED`, `SNAPSHOTS_EMITTED`, `ENTRIES_READ`, `ENTRIES_KEPT`, `SEGMENTS_DROPPED`.
11. **Set daemon status** to `RUNNING` during the cycle, then `IDLE` at end via `daemon_state`.
12. **Print contract** via `summary_printer/print-summary` reading from `stats->alist` + computed ratios — no hard-coded numbers.

The contract `DAEMON_STATUS=IDLE` is read from the daemon after the cycle completes; `CYCLES_RUN` from the cycle counter; `COLD_THRESHOLD` is passed through; the rest come from stats alist + byte math.

---

## 4. Anti-hardcode checklist

`main.aura` MUST:
- Build every segment/entry through `make-segment` / `make-entry`.
- Derive every printed value from an API result or arithmetic on API results.
- NOT contain literal integers assigned to any `KEY=` line (e.g. no `(display "SEGMENTS_SCANNED=5")`).
- Use `summary_printer/format-key-value` or equivalent list traversal to emit each line.
- Use `daemon_state/daemon-status` (live state) for the `DAEMON_STATUS` line, not a string literal.
- Use `cycle_counter/cycle-count` (live counter) for `CYCLES_RUN`.

A reviewer can confirm by deleting one cold segment from the build step — output values must shift, but the key set/order stays identical.

---

## 5. How to run

```sh
aura wal_segment.aura wal_entry.aura wal_log.aura \
     cold_detector.aura merger.aura tombstone_sweeper.aura \
     snapshot_writer.aura byte_counter.aura cycle_counter.aura \
     stats_collector.aura summary_printer.aura daemon_state.aura \
     main.aura
json dogfood
{"files":["wal_segment.aura","wal_entry.aura","wal_log.aura","cold_detector.aura","merger.aura","tombstone_sweeper.aura","snapshot_writer.aura","byte_counter.aura","cycle_counter.aura","stats_collector.aura","summary_printer.aura","daemon_state.aura","main.aura"],"entry":"main.aura","run_mode":"cli_multi","expect_keys":["SEGMENTS_SCANNED","SEGMENTS_MERGED","SEGMENTS_DROPPED","ENTRIES_READ","ENTRIES_KEPT","TOMBSTONES_DROPPED","SNAPSHOTS_EMITTED","BYTES_BEFORE","BYTES_AFTER","COMPRESSION_RATIO","COLD_THRESHOLD","CYCLES_RUN","DAEMON_STATUS"],"source_res":["\\(define\\s+\\(make-segment\\b","\\(define\\s+\\(make-entry\\b","\\(define\\s+\\(make-log\\b","\\(define\\s+\\(classify-cold\\b","\\(define\\s+\\(merge-segments\\b","\\(define\\s+\\(sweep-tombstones\\b","\\(define\\s+\\(write-snapshot\\b","\\(define\\s+\\(compression-ratio\\b","\\(define\\s+\\(cycle-tick\\b","\\(define\\s+\\(make-stats\\b","\\(define\\s+\\(print-summary\\b","\\(define\\s+\\(make-daemon\\b"]}
```
