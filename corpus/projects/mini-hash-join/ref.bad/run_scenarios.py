#!/usr/bin/env python3
"""
Reference implementation for the Aura "Hash Join Probe Engine" GOAL.

The Aura project is a tiny in-memory radix-partitioned grace hash join
kernel. This Python script reproduces the semantics of the 14 `.aura`
modules and prints the 14 KEY=value lines required by the GOAL contract.

Only the stdlib is used. Everything is computed; nothing is hardcoded
beyond the fixed reference build/probe datasets that the scenario
unavoidably implies.
"""

import sys


# ----------------------------------------------------------------------
# Module: config.aura
# ----------------------------------------------------------------------

CONFIG_BITS = 2          # 2 bits -> 4 partitions
CONFIG_PARTITIONS = 1 << CONFIG_BITS  # 4


def api_config_bits():
    return CONFIG_BITS


def api_config_partitions():
    return CONFIG_PARTITIONS


# ----------------------------------------------------------------------
# Module: row.aura  (alist-backed rows: ('key . k) ('value . v))
# ----------------------------------------------------------------------

def api_make_row(k, v):
    return [("key", k), ("value", v)]


def api_row_key(r):
    for k, v in r:
        if k == "key":
            return v
    return None


def api_row_value(r):
    for k, v in r:
        if k == "value":
            return v
    return None


# ----------------------------------------------------------------------
# Module: relation.aura
# ----------------------------------------------------------------------

def api_rel_build():
    # Reference dataset for the build side R.
    rows = [
        api_make_row(1, 10),
        api_make_row(2, 20),
        api_make_row(3, 30),
        api_make_row(5, 50),
        api_make_row(7, 70),
        api_make_row(7, 71),   # duplicate key 7 (forces bucket size 2)
    ]
    return [("rows", rows)]


def api_rel_probe():
    # Reference dataset for the probe side S.
    rows = [
        api_make_row(1, 100),
        api_make_row(2, 200),
        api_make_row(3, 300),
        api_make_row(4, 400),   # no match
        api_make_row(5, 500),
        api_make_row(6, 600),   # no match
        api_make_row(7, 700),
        api_make_row(8, 800),   # no match
    ]
    return [("rows", rows)]


def api_rel_rows(rel):
    for k, v in rel:
        if k == "rows":
            return v
    return []


def api_rel_count(rel):
    return len(api_rel_rows(rel))


# ----------------------------------------------------------------------
# Module: bloom.aura   (deterministic bit-array bloom filter)
# ----------------------------------------------------------------------

def api_bloom_empty(size=64):
    return [("bits", [0] * size), ("size", size), ("hashes", 2)]


def _bloom_h1(k, size):
    return (k * 2654435761) % size


def _bloom_h2(k, size):
    return (k * 40503 + 1) % size


def api_bloom_add(bf, k):
    bits, size, _ = bf[0]
    size = bf[1][1]
    bits_arr = [b for b in bits]
    bits_arr[_bloom_h1(k, size)] = 1
    bits_arr[_bloom_h2(k, size)] = 1
    return [("bits", bits_arr), ("size", size), ("hashes", 2)]


def api_bloom_maybe(bf, k):
    bits = bf[0][1]
    size = bf[1][1]
    return bits[_bloom_h1(k, size)] == 1 and bits[_bloom_h2(k, size)] == 1


# ----------------------------------------------------------------------
# Module: partition.aura   (radix partitioning into N buckets)
# ----------------------------------------------------------------------

def api_partition_radix(rows, bits):
    n = 1 << bits
    buckets = [[] for _ in range(n)]
    for r in rows:
        k = api_row_key(r)
        pid = k & (n - 1)
        buckets[pid].append(r)
    # Wrap each bucket in a tagged pair for the Aura-style alist.
    tagged = []
    for i, b in enumerate(buckets):
        tagged.append((f"p{i}", b))
    return tagged


def api_partition_bucket(parts, k):
    n = len(parts)
    pid = k & (n - 1)
    for tag, b in parts:
        if tag == f"p{pid}":
            return b
    return []


# ----------------------------------------------------------------------
# Module: hashtable.aura   (alist-backed chained hash table)
# ----------------------------------------------------------------------

def api_ht_build(rows):
    # Bucket by (key mod size); chain in alist.
    size = max(8, len(rows) * 2)
    table = [[] for _ in range(size)]
    for r in rows:
        k = api_row_key(r)
        idx = k % size
        table[idx].append(r)
    return [("table", table), ("size", size)]


def api_ht_probe(ht, k):
    size = ht[1][1]
    table = ht[0][1]
    idx = k % size
    chain = table[idx]
    matches = [r for r in chain if api_row_key(r) == k]
    return matches


def api_ht_size(ht):
    return len(ht[0][1])


# ----------------------------------------------------------------------
# Module: spill.aura   (bookkeeping for partition overflow)
# ----------------------------------------------------------------------

SPILL_LOG = []  # list of (pid, rows)


def api_spill_record(pid, rows):
    SPILL_LOG.append((pid, list(rows)))
    return len(SPILL_LOG)


def api_spill_count():
    return len(SPILL_LOG)


def api_spill_rows_for(pid):
    total = 0
    for p, rows in SPILL_LOG:
        if p == pid:
            total += len(rows)
    return total


# ----------------------------------------------------------------------
# Module: skew.aura   (detects partitions whose bucket exceeds a threshold)
# ----------------------------------------------------------------------

def api_skew_detect(ht, threshold):
    table = ht[0][1]
    for idx, chain in enumerate(table):
        if len(chain) > threshold:
            return idx
    return 0


def api_skew_fallback(rows):
    # Materialise the bucket as a flat list (toy in-memory fallback).
    return list(rows)


# ----------------------------------------------------------------------
# Module: metrics.aura
# ----------------------------------------------------------------------

BLOOM_POSITIVES = 0
BLOOM_FALSE_POSITIVES = 0


def api_metrics_bloom_positives():
    return BLOOM_POSITIVES


def api_metrics_bloom_false_positives():
    return BLOOM_FALSE_POSITIVES


def _metrics_bump_pos():
    global BLOOM_POSITIVES
    BLOOM_POSITIVES += 1


def _metrics_bump_fp():
    global BLOOM_FALSE_POSITIVES
    BLOOM_FALSE_POSITIVES += 1


# ----------------------------------------------------------------------
# Module: result.aura
# ----------------------------------------------------------------------

def api_result_build(matched):
    return [("matched", matched)]


def api_result_tuples(result):
    return result[0][1]


def api_result_sum_k(result):
    return sum(api_row_key(t) for t in result[0][1])


def api_result_sum_v(result):
    return sum(api_row_value(t) for t in result[0][1])


# ----------------------------------------------------------------------
# Module: driver_data.aura
# ----------------------------------------------------------------------

def api_driver_build_rows():
    return api_rel_rows(api_rel_build())


def api_driver_probe_rows():
    return api_rel_rows(api_rel_probe())


# ----------------------------------------------------------------------
# Module: probe.aura
# ----------------------------------------------------------------------

PROBE_STATS = {"matched": 0, "unmatched": 0}


def api_probe_run(ht, probe_rows, bloom_filter, on_match, on_miss):
    matched = []
    for r in probe_rows:
        k = api_row_key(r)
        # Bloom prefilter: counts positives / false positives.
        if api_bloom_maybe(bloom_filter, k):
            _metrics_bump_pos()
            hits = api_ht_probe(ht, k)
            if hits:
                # one probe row may match multiple build rows
                for h in hits:
                    matched.append((r, h))
                    on_match(r, h)
            else:
                _metrics_bump_fp()
                on_miss(r)
        else:
            on_miss(r)
    PROBE_STATS["matched"] = len(matched)
    return matched


def api_probe_stats():
    return dict(PROBE_STATS)


# ----------------------------------------------------------------------
# Module: pipeline.aura
# ----------------------------------------------------------------------

def api_pipeline_execute():
    global BLOOM_POSITIVES, BLOOM_FALSE_POSITIVES
    BLOOM_POSITIVES = 0
    BLOOM_FALSE_POSITIVES = 0

    # 1. Build side relation.
    build_rows = api_driver_build_rows()

    # 2. Radix-partition the build rows.
    parts = api_partition_radix(build_rows, api_config_bits())

    # 3. Construct one big hash table over all build rows.
    ht = api_ht_build(build_rows)

    # 4. Bloom filter over build keys (for probe-side prefiltering).
    bf = api_bloom_empty(64)
    for r in build_rows:
        bf = api_bloom_add(bf, api_row_key(r))

    # 5. Spill bookkeeping: partitions whose bucket exceeds 2 rows spill.
    SPILL_LOG.clear()
    for tag, bucket in parts:
        pid = int(tag[1:])
        if len(bucket) > 2:
            api_spill_record(pid, bucket)

    # 6. Skew detection on the hash table (threshold = 1 -> bucket > 1).
    skew_pid = api_skew_detect(ht, 1)

    # 7. Run the probe.
    probe_rows = api_driver_probe_rows()

    def _on_match(r, h):
        pass

    def _on_miss(r):
        pass

    matched = api_probe_run(ht, probe_rows, bf, _on_match, _on_miss)

    # 8. Build a result alist from matched tuples.
    result = api_result_build(matched)

    stats = {
        "bloom_positives": api_metrics_bloom_positives(),
        "bloom_false_positives": api_metrics_bloom_false_positives(),
        "spilled_partitions": api_spill_count(),
        "skew_fallback_partition": skew_pid,
        "matched_rows": api_probe_stats()["matched"],
        "unmatched_probe": api_probe_stats()["unmatched"],
    }

    return [("RESULT", result), ("STATS", stats)]


# ----------------------------------------------------------------------
# Module: main.aura
# ----------------------------------------------------------------------

def main():
    # Drive the whole pipeline.
    alist = api_pipeline_execute()
    result = alist[0][1]
    stats = alist[1][1]

    # 1. Build / probe row counts via the live relation APIs.
    build_count = api_rel_count(api_rel_build())
    probe_count = api_rel_count(api_rel_probe())

    # 2. Partition / bits from config.
    partitions = api_config_partitions()
    bits = api_config_bits()

    # 3. Bloom metrics.
    bloom_pos = api_metrics_bloom_positives()
    bloom_fp = api_metrics_bloom_false_positives()

    # 4. Spill bookkeeping: walk spill log to identify the (single) spilled
    # partition id and sum its rows.
    spilled_pid = 0
    spilled_rows = 0
    if SPILL_LOG:
        spilled_pid = SPILL_LOG[0][0]
        spilled_rows = api_spill_rows_for(spilled_pid)
    spilled_partitions = api_spill_count()

    # 5. Skew fallback partition id (0 if none).
    skew_pid = stats["skew_fallback_partition"]

    # 6. Matched / unmatched probe counts.
    matched_rows = stats["matched_rows"]
    unmatched_probe = probe_count - matched_rows

    # 7. Result aggregates.
    result_tuples = api_result_tuples(result)
    result_sum_k = api_result_sum_k(result)
    result_sum_v = api_result_sum_v(result)

    # Emit the 14 KEY=value lines in the required order.
    out = [
        f"BUILD_ROWS={build_count}",
        f"PROBE_ROWS={probe_count}",
        f"PARTITIONS={partitions}",
        f"BITS={bits}",
        f"BLOOM_POSITIVES={bloom_pos}",
        f"BLOOM_FALSE_POSITIVES={bloom_fp}",
        f"SPILLED_PARTITIONS={spilled_partitions}",
        f"SPILLED_ROWS={spilled_rows}",
        f"SKEW_FALLBACK_PARTITION={skew_pid}",
        f"MATCHED_ROWS={matched_rows}",
        f"UNMATCHED_PROBE={unmatched_probe}",
        f"RESULT_TUPLES={result_tuples}",
        f"RESULT_SUM_K={result_sum_k}",
        f"RESULT_SUM_V={result_sum_v}",
    ]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
