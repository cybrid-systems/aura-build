# mini-wal-zstd-frames — Compressed WAL with Frame Dictionary

A toy Write-Ahead Log (WAL) implementation in Aura. Records are framed into CRC32-checksummed
blocks, dictionary-compressed with a small rolling-window dictionary (a `mini-zstd`-style approach),
and written block-aligned to an in-memory byte stream. Tail frames are partially readable so the
last partial write can be inspected without decompressing earlier frames.

The project demonstrates:

- Frame format: `[MAGIC(2) | VER(1) | FLAGS(1) | CRC32(4) | DICT_ID(2) | RAW_LEN(2) | COMP_LEN(2) | PAYLOAD]`
- Rolling dictionary training from recent literals (last 8 KB window)
- Dictionary compression: literal / back-reference (offset, length) tokens
- CRC32 over the **decompressed** payload (cheaper to verify on partial tail read)
- Partial tail read: only the last (possibly incomplete) frame is decoded
- Round-trip integrity: every record is recoverable

## Stdout contract (exact, in order)



13 keys. Values are measured by a Python reference; **the Aura program must compute them by calling
the module APIs**, not by hard-coding the strings above.

## Module table

| File | Required exported API (top-level `define` forms) |
|------|---------------------------------------------------|
| `crc32.aura` | `(crc32-init)`, `(crc32-update crc byte)`, `(crc32-final crc)`, `(crc32 buf)` |
| `bytebuf.aura` | `(make-bytebuf)`, `(bb-put! bb b)`, `(bb-get! bb)`, `(bb-pos bb)`, `(bb-slice bb n)`, `(bb-len bb)`, `(bb-bytes bb)` |
| `dict.aura` | `(dict-init capacity)`, `(dict-train! dict literals)`, `(dict-id dict)`, `(dict-window dict)` |
| `codec.aura` | `(codec-compress dict bytes)`, `(codec-decompress dict framed)`, `(codec-bytes-out)`, `(codec-bytes-in)` |
| `frame.aura` | `(frame-magic)`, `(frame-version)`, `(frame-encode dict payload)`, `(frame-decode dict framed)`, `(frame-crc framed)`, `(frame-raw-len framed)` |
| `wal.aura` | `(wal-open)`, `(wal-append! wal key value)`, `(wal-flush-block! wal)`, `(wal-read-tail wal)`, `(wal-replay wal)`, `(wal-frames wal)`, `(wal-raw-bytes wal)`, `(wal-stored-bytes wal)`, `(wal-records wal)` |
| `stats.aura` | `(stats-new)`, `(stats-on-frame! st raw stored)`, `(stats-dump st)`, `(stats-ratio st)` |
| `keys.aura` | `(key-first wal)`, `(key-last wal)`, `(key-count wal)` |
| `hex.aura` | `(hex-of-byte b)`, `(hex-of-word n)` |
| `logfmt.aura` | `(logfmt kv-alist)`, `(logfmt-line k v)` |
| `report.aura` | `(report-wal wal st)`, `(report-key-first k)`, `(report-key-last k)` |
| `main.aura` | (driver; computes everything via module APIs and prints the 13 keys above) |

## Scenario steps (executed by `main.aura`)

1. Load `crc32.aura`, build the table, and verify CRC32("abc") == 0x352441C2 (sanity print absorbed into init).
2. Load `bytebuf.aura` and construct the underlying in-memory block store; record `bb-pos` after each `wal-flush-block!`.
3. Load `dict.aura`, train a dictionary from the first ~2 KB of synthetic literals; pin `dict-id`.
4. Load `codec.aura`; assert round-trip `codec-decompress(dict, codec-compress(dict, x)) == x` on a sample record.
5. Load `frame.aura`; encode/decode one frame and verify `frame-crc` matches `crc32(decompressed)`.
6. Load `wal.aura`:
   - `wal-open` with default block size 4096 and dict cap 2048.
   - Append 42 records `user:1001..user:1042`, each `"op=put ts=N"`.
   - After every 4096 raw bytes, `wal-flush-block!` to emit a frame.
   - Call `wal-read-tail` and assert `WAL_TAIL_PARTIAL=#t`.
   - Call `wal-replay` and assert `WAL_REPLAY_MATCH=#t`.
7. Load `stats.aura`; record `WAL_BYTES_RAW` and `WAL_BYTES_STORED` via `stats-ratio`.
8. Load `keys.aura`; pull `user:1001` and `user:1042` from the WAL via `key-first`/`key-last`.
9. Load `hex.aura` + `logfmt.aura`; use `report-wal` to format the final key=value stdout.

The 13 stdout keys are produced **only after** the API calls above complete. Replacing any module call
with a literal will desynchronize the program — for example, the partial-tail flag depends on the
last frame being smaller than the block, which only holds when `wal-read-tail` actually walks frames.

## Anti-hardcode checks

- `WAL_FRAMES` must come from `wal-frames`; it equals 6 only because 42 records at ~64 bytes each
  fill exactly five 4096-byte blocks plus one short tail frame.
- `WAL_CRC_OK` must be derived by recomputing `crc32` on the decompressed tail and comparing with
  `frame-crc`.
- `WAL_REPLAY_MATCH` must be `(equal? (wal-replay wal) original-records)`.
- `WAL_FIRST_KEY` / `WAL_LAST_KEY` come from `key-first`/`key-last`, not literals.

## How to run



The Aura CLI loads each file in order into a shared top-level, then evaluates `main.aura`.
