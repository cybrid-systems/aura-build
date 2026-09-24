# WAL Record CRUD — Versioned Codec Mini Project

## Overview

A tiny in-memory **write-ahead-log (WAL) record codec** with **schema versioning**.
Records carry a schema-id and a list of `(tag . value)` fields. The codec can:

* encode records to a portable **s-expression byte-string** (a list of symbols/numbers/strings),
* decode them back,
* **migrate forward** when the reader schema adds new (additive) columns,
* **migrate backward** by skipping / defaulting unknown columns.

This is the kind of codec you would prototype before committing to a real binary format.
All state lives in lists / alists; no I/O beyond `display` / `newline`.

## Stdout contract (exact order)

The run MUST print these `KEY=value` lines, in this order, one per line:



(Values are measured by a reference Python impl; this Aura project must reproduce them
by actually calling the module APIs.)

## Module table

| File                | Required exported `define`s                                                                                                                                                  |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `wal-types.aura`    | `(api wal-version)`, `(api make-tag)`, `(api tag? t)`, `(api tag-name t)`, `(api tag-type t)`, `(api make-record sid fields)`, `(api record-schema-id r)`, `(api record-fields r)` |
| `wal-schema.aura`   | `(api define-schema id fields)`, `(api schema-exists? id)`, `(api schema-fields id)`, `(api schema-type id tag)`, `(api all-schemas)`, `(api latest-schema-id)`                |
| `wal-encode.aura`   | `(api encode-record r)`, `(api encode-field f)`, `(api encode-value v type)`                                                                                                  |
| `wal-decode.aura`   | `(api decode-record s)`, `(api decode-field tok)`, `(api decode-value tok type)`                                                                                              |
| `wal-migrate.aura`  | `(api migrate-record r from-id to-id)`, `(api forward-fill r from-id to-id)`, `(api backward-strip r from-id to-id)`                                                         |
| `wal-store.aura`    | `(api store-clear)`, `(api store-append r)`, `(api store-all)`, `(api store-count)`, `(api store-nth i)`                                                                      |
| `wal-bytes.aura`    | `(api encoded-length s)`, `(api join-encoded xs)`, `(api payload-bytes store)`                                                                                                |
| `wal-defaults.aura` | `(api default-value type)`, `(api known-types)`                                                                                                                               |
| `wal-main-helpers.aura` | `(api setup-schemas)`, `(api build-sample-records)`, `(api run-roundtrip)`, `(api count-migrations)`, `(api collect-stats)`, `(api format-stats alist)`                |
| `stats.aura`        | `(api stat-new k v)`, `(api stat-set! alist k v)`, `(api stat-get alist k)`, `(api stat-keys alist)`                                                                          |
| `main.aura`         | (entry) orchestrates the scenario and prints the 11 KEY=value lines                                                                                                            |

## Scenario steps (executed by `main.aura`)

1. **Init** — call `(wal-store-clear)` and `(wal-version)`.
2. **Schema setup** — call `(setup-schemas)` which internally invokes `define-schema` for
   schema 1 (id, name), schema 2 (+ email), schema 3 (+ email, phone, age).
   Capture the returned count into `schemas-defined`.
3. **Build sample records** — `(build-sample-records)` returns a list of 6 records
   covering all three schema ids, including one that intentionally uses a future
   column to exercise migration.
4. **Encode** — for each record call `(wal-encode-record r)`; push the encoded form
   into a parallel "encoded" list. Increment `records-encoded`.
5. **Decode** — for each encoded form call `(wal-decode-record s)`; push the decoded
   record into the store via `(store-append)`. Increment `records-decoded`.
6. **Migration passes**
   * `(run-roundtrip)` — re-decode every encoded form, re-encode, compare structurally
     (`equal?`) to the original encoded form. Record `round-trip-ok = #t/#f`.
   * `(count-migrations)` — for every record whose stored schema-id differs from
     `(latest-schema-id)`, call `(migrate-record ... to-id)` (forward) or
     `(migrate-record ... from=latest to=oldest)` for the one future-tagged record
     (backward). Tally `forward-migrations` and `backward-migrations`.
7. **Stats** — `(collect-stats)` walks the store and produces an alist:
   `oldest-schema`, `newest-schema`, `latest-record-tag` (the tag of the last field of
   the last record), `total-bytes` (sum of `encoded-length` over all original encodings).
8. **Print** — `(format-stats alist)` plus the precomputed counters emits the 11
   `KEY=value` lines in the exact order above.

## Anti-hardcode guard

`main.aura` must NOT just `display` the expected strings. Every value must be obtained by
calling at least one module API:

* `WAL_VERSION` ← `(wal-version)`
* `SCHEMAS_DEFINED` ← returned by `(setup-schemas)`
* `RECORDS_ENCODED` / `RECORDS_DECODED` / `FORWARD_MIGRATIONS` / `BACKWARD_MIGRATIONS`
  ← incremented from `(store-append)`, `(wal-decode-record)`, `(migrate-record)`
* `ROUND_TRIP_OK` ← result of `(run-roundtrip)`
* `OLDEST_SCHEMA` / `NEWEST_SCHEMA` / `LATEST_RECORD_TAG` / `TOTAL_BYTES`
  ← computed by `(collect-stats)`

A submission that hardcodes the printed numbers while skipping the APIs is invalid.

## How to run



All files share one top-level environment (loaded left-to-right). `main.aura` is last
and performs the `display` calls.
