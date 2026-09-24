```markdown
# Encrypted WAL with Key Rotation (mini-wal-encrypt)

## Overview
A toy in-memory write-ahead log (WAL) that simulates per-segment authenticated
encryption with a rolling key-version scheme. Keys are versioned and rotated
periodically; the WAL tracks which key version encrypted each segment, and
simulates a re-key pass that runs as part of compaction. Segment integrity is
verified by a SHA-style truncated hash over ciphertext (stand-in for an HMAC),
and tampering causes a verification failure. All state is kept in memory using
Aura lists and alists — no file I/O, no Python, no records.

## Stdout contract (KEY=value, exact order)
The program must print exactly these lines on stdout, in this order, computed
by calling APIs from the modules below (no hardcoded strings):



## Module table

| File | Required exported `define`s (APIs) |
|---|---|
| `keys.aura` | `(api-keys-make-init)` → alist of version→bytes; `(api-keys-current ks)` → current version number; `(api-keys-rotate ks)` → new ks with new current version; `(api-keys-version-bytes ks v)` → bytes for a version |
| `cipher.aura` | `(api-cipher-seal key bytes)` → ciphertext cons cell (header . body); `(api-cipher-open key ct)` → bytes or `#f` on failure; `(api-cipher-tag ct)` → truncated hash string |
| `wal.aura` | `(api-wal-new keys)` → empty wal; `(api-wal-append wal key-version bytes)` → updated wal with new segment (auto-segments); `(api-wal-segs wal)` → segment count; `(api-wal-records wal)` → total record count; `(api-wal-lsn-range wal)` → (min-lsn . max-lsn) pair; `(api-wal-verify wal keys)` → list of tampered segment indices; `(api-wal-seal-version wal seg-idx)` → key version used to seal segment |
| `compact.aura` | `(api-compact-rekey wal keys threshold)` → runs re-key pass; returns `(new-wal . new-keys . stats)` where stats is `(rekeyed-segments . reencrypted-records)`; `(api-compact-lag old-wal new-wal)` → segments dropped |
| `tamper.aura` | `(api-tamper-flip-bit wal seg-idx)` → flipped wal; `(api-tamper-key-version wal seg-idx new-v)` → wal with header rewrite |
| `stats.aura` | `(api-stats-active-key-range wal)` → `(min-seg-with-current . max-seg-with-current)` |
| `main.aura` | orchestrates scenario; prints all KEY=value lines |

## Scenario steps (run from `main.aura`)

1. Build an initial keyring with 2 versions via `api-keys-make-init`.
2. Create an empty wal via `api-wal-new`.
3. Append 120 records, splitting into 8 segments of 15 records each (15 bytes
   payload per record); segment 1 uses key v1, segments 2–3 use v1, then rotate
   keys so segment 4 uses v2, segments 5–6 use v2, then rotate to v3 for
   segment 7, and rotate to v4 for segment 8. (3 rotations total.)
4. Verify wal integrity via `api-wal-verify` — should report 0 tampered
   segments.
5. Tamper two distinct segments via `api-tamper-flip-bit`; re-verify — should
   report exactly those 2 tampered segments.
6. Run compaction/re-key via `api-compact-rekey` with threshold that forces
   the oldest 2 segments (sealed with v1) to be re-encrypted under the current
   key version.
7. Re-verify after re-key — all segments should verify cleanly (tamper list
   empty after restoring — note we recompute on the post-rekey wal).
8. Compute stats via `api-stats-active-key-range` — segments sealed under the
   current key version (the post-rekey v4) should range across all segments
   from min to max = 8.
9. Compute lag via `api-compact-lag` — with no segments dropped, lag = 0.
10. Print all 13 KEY=value lines in the exact order above.

## Anti-hardcode notes
- All numeric values (segment counts, LSNs, key versions, rotation counts,
  re-key counts, tamper counts, verified counts, lag, active-key range) must
  be obtained by calling the module APIs above. `main.aura` is not allowed to
  embed the expected numbers as literals next to a `display` call.
- The wal itself is the source of truth for segments/records/lsn — derived
  stats are computed from `api-wal-*` calls, not hardcoded.
- Tampered segment count must be derived from `api-wal-verify` output, not a
  literal `2`.
- The rekeyed/reencrypted stats must be derived from `api-compact-rekey`'s
  returned stats list, not literals.

## How to run



Each file shares one top-level environment; later files see earlier `define`s.

## Implementation hints
- Use plain lists of byte values (small integers 0–255) for ciphertext "bytes".
- "Encryption" can be a reversible XOR with a per-version repeating key derived
  from the version number; the tag is `(modulo (foldl + 0 (car ct)) 1000000)`
  or similar deterministic truncated hash. Tampering = flipping a bit in the
  ciphertext body, which the XOR + tag check should catch.
- A segment is a list of (lsn . ciphertext) entries plus a header holding
  `(key-version . segment-index . tag)`.
- "Append" splits into a new segment when the current segment hits 15 records.
- Re-key pass walks segments from oldest, re-sealing any whose stored
  key-version differs from the current key version, until the re-key budget
  (= threshold) is exhausted.
json dogfood
{
  "files": [
    "keys.aura",
    "cipher.aura",
    "wal.aura",
    "compact.aura",
    "tamper.aura",
    "stats.aura",
    "main.aura"
  ],
  "entry": "main.aura",
  "run_mode": "cli_multi",
  "expect_keys": [
    "wal_segs",
    "wal_records",
    "wal_key_current",
    "wal_rotations",
    "wal_rekeyed",
    "wal_reencrypted",
    "wal_verified",
    "wal_tamper_detected",
    "wal_lsn_first",
    "wal_lsn_last",
    "wal_active_key_seg_min",
    "wal_active_key_seg_max",
    "wal_lag_segs"
  ],
  "source_res": [
    "\\(define\\s+\\(api-keys-make-init\\b",
    "\\(define\\s+\\(api-keys-current\\b",
    "\\(define\\s+\\(api-keys-rotate\\b",
    "\\(define\\s+\\(api-keys-version-bytes\\b",
    "\\(define\\s+\\(api-cipher-seal\\b",
    "\\(define\\s+\\(api-cipher-open\\b",
    "\\(define\\s+\\(api-cipher-tag\\b",
    "\\(define\\s+\\(api-wal-new\\b",
    "\\(define\\s+\\(api-wal-append\\b",
    "\\(define\\s+\\(api-wal-segs\\b",
    "\\(define\\s+\\(api-wal-records\\b",
    "\\(define\\s+\\(api-wal-lsn-range\\b",
    "\\(define\\s+\\(api-wal-verify\\b",
    "\\(define\\s+\\(api-wal-seal-version\\b",
    "\\(define\\s+\\(api-compact-rekey\\b",
    "\\(define\\s+\\(api-compact-lag\\b",
    "\\(define\\s+\\(api-tamper-flip-bit\\b",
    "\\(define\\s+\\(api-tamper-key-version\\b",
    "\\(define\\s+\\(api-stats-active-key-range\\b"
  ]
}
```
