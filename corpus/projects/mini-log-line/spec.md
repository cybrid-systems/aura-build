# Mini-Log-Line

A tiny parser for a stream of lines where each line is **either** logfmt (`key=value key="quoted val"`) **or** JSON-line (single-line JSON object). The parser auto-detects the dialect per line, normalizes both into a common record `'(timestamp level service message)`, and supports grep-style field projection (`level=ERROR`).

---

## Stdout contract (KEY=value lines, exact order)



That's 12 keys. The scenario must print them in this order with these exact key names.

---

## Module table

| File | Required exported `define`s |
|------|------------------------------|
| `src/detect.aura` | `(detect-dialect line)` → symbol `logfmt` or `json` |
| `src/scan.aura`   | `(scan-line line)` → alist of `(key . value)` (both strings) |
| `src/logfmt.aura` | `(parse-logfmt line)` → alist; `(encode-logfmt alist)` → string |
| `src/jsonline.aura`| `(parse-jsonline line)` → alist (flattens one level of nesting with `.` join); `(encode-jsonline alist)` → string |
| `src/normalize.aura` | `(normalize dialect alist)` → `'(timestamp level service message)` (strings, `#f` when missing) |
| `src/project.aura` | `(matches? record predicate)` → boolean; `(parse-predicate pred-str)` → `(field . want)` |
| `src/stream.aura` | `(parse-stream lines)` → list of records; `(project-stream records predicates)` → filtered list |
| `src/greputil.aura` | `(split-string s sep)` / `(trim s)` / `(has-char? s c)` — string helpers |
| `src/testdata.aura` | `(sample-lines)` → list of 6 mixed lines; `(expected-projection)` → 2 predicate strings |
| `main.aura`       | Driver: loads sample stream, runs APIs, prints the 12 keys above |

All files share one top-level; load order is the order listed. `main.aura` is the entry point and must be last.

---

## Scenario steps (`main.aura`)

1. Load 6 sample lines from `testdata.aura`:
   - 3 logfmt lines, 3 JSON-line lines, interleaved.
2. For lines 1 and 2, call `(detect-dialect line)` and `display` `DIALECT_DETECTED=<sym>`.
3. Call `(parse-stream sample-lines)` → list of normalized records. Count with a length helper; `display` `NORMALIZED_COUNT=<n>` (must be 6).
4. Take the 1st record, project field `level` via `normalize` record access; print `FIELD_LEVEL=ERROR`.
5. Take the 2nd record, project field `level`; print `FIELD_LEVEL=INFO`.
6. Take the 3rd record, project field `service`; print `FIELD_SERVICE=auth`.
7. Take the 4th record, project field `service`; print `FIELD_SERVICE=billing`.
8. Build two predicates from `(expected-projection)`, call `(project-stream records predicates)`. Print `PROJECTION_COUNT=<len filtered-after-p1>` and `PROJECTION_COUNT=<len filtered-after-p2>`.
9. On the raw logfmt sample, check that scanning yielded at least one value containing a space (quoted); print `HAS_QUOTED_VALUE=true`.
10. On the raw JSON sample, check that scanning yielded at least one key containing `.` (flattened nesting); print `HAS_NESTED_JSON=true`.
11. Round-trip: re-encode one logfmt record and one JSON record via their `encode-*` APIs, re-parse, compare with `equal?`; print `ROUNDTRIP_OK=true`.

---

## Anti-hardcode

`main.aura` must:
- Actually call `(detect-dialect …)`, `(parse-stream …)`, `(project-stream …)`, and the `encode-*` functions.
- Derive every printed value from those return values — no literal numbers or strings for counts or field contents.
- The `FIELD_LEVEL=ERROR` / `FIELD_SERVICE=auth` values come from the parsed records, not from string constants in `main.aura`.

---

## How to run



Aura loads each file in order on one CLI invocation; top-level `define`s carry across files.

---
