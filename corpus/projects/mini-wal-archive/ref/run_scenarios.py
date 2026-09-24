#!/usr/bin/env python3
"""Reference implementation of the tiered WAL archiver scenario."""

# --- Toy in-memory semantics ---

_CLOCK_MS = 0
_LOG = []

def current_ms():
    return _CLOCK_MS

def advance_ms(n):
    global _CLOCK_MS
    _CLOCK_MS += n

def log_event(evt):
    _LOG.append(evt)

def drain_log():
    return '|'.join(_LOG)

class Segment:
    __slots__ = ('sid', 'nbytes', 'ingested_at_ms', 'tier')
    def __init__(self, sid, nbytes, ingested_at_ms, tier='hot'):
        self.sid = sid
        self.nbytes = nbytes
        self.ingested_at_ms = ingested_at_ms
        self.tier = tier

class Store:
    def __init__(self, tier):
        self.tier = tier
        self.segments = []
    def add(self, seg):
        seg.tier = self.tier
        self.segments.append(seg)
    def all(self):
        return list(self.segments)
    def size(self):
        return len(self.segments)
    def total_bytes(self):
        return sum(s.nbytes for s in self.segments)
    def oldest_age_ms(self):
        if not self.segments:
            return 0
        return _CLOCK_MS - min(s.ingested_at_ms for s in self.segments)
    def remove_by_ids(self, ids):
        ids_set = set(ids)
        removed = [s for s in self.segments if s.sid in ids_set]
        self.segments = [s for s in self.segments if s.sid not in ids_set]
        return removed
    def remove_segment(self, seg):
        self.segments.remove(seg)

def make_segment(sid, nbytes, ingested_at_ms):
    return Segment(sid, nbytes, ingested_at_ms)

def segment_age_ms(seg):
    return _CLOCK_MS - seg.ingested_at_ms

def default_config():
    return {'archive_age_ms': 5000, 'archive_bytes': 10000, 'retain_max': 5}

def ingest_segment(store, seg):
    store.add(seg)
    log_event('ingest')

def age_sweep(store, cfg):
    threshold = cfg['archive_age_ms']
    candidates = [s for s in store.all() if segment_age_ms(s) >= threshold]
    log_event('age-sweep')
    return candidates

def archive_sweep(hot, cold, cfg):
    threshold = cfg['archive_age_ms']
    moved = [s for s in list(hot.segments) if segment_age_ms(s) >= threshold]
    for s in moved:
        hot.remove_segment(s)
        cold.add(s)
    log_event('archive-sweep')
    return {'count': len(moved), 'bytes': sum(s.nbytes for s in moved)}

def enforce_retention(store, cfg):
    retain = cfg['retain_max']
    all_segs = sorted(store.all(), key=lambda s: s.sid)
    if len(all_segs) <= retain:
        log_event('retention')
        return {'dropped_count': 0, 'dropped_bytes': 0, 'retained': len(all_segs)}
    to_drop = all_segs[:len(all_segs) - retain]
    drop_ids = [s.sid for s in to_drop]
    removed = store.remove_by_ids(drop_ids)
    log_event('retention')
    return {
        'dropped_count': len(removed),
        'dropped_bytes': sum(s.nbytes for s in removed),
        'retained': store.size(),
    }

def compute_stats(hot, cold):
    return {
        'hot_segments': hot.size(),
        'hot_bytes': hot.total_bytes(),
        'cold_segments': cold.size(),
        'cold_bytes': cold.total_bytes(),
        'total_segments': hot.size() + cold.size(),
        'total_bytes': hot.total_bytes() + cold.total_bytes(),
        'hot_oldest_age_ms': hot.oldest_age_ms(),
        'cold_oldest_age_ms': cold.oldest_age_ms(),
    }

def run_archive_pipeline(hot, cold, cfg):
    global _CLOCK_MS, _LOG
    _CLOCK_MS = 0
    _LOG = []
    log_event('ingest')  # prime
    SEG_BYTES = 10000
    for i in range(1, 11):
        advance_ms(1000)
        seg = make_segment(i, SEG_BYTES, _CLOCK_MS)
        ingest_segment(hot, seg)
    # Let the oldest 7 segs (ids 1-7, ingested at t=1000..7000) age past 5000ms
    advance_ms(2000)  # now t=12000
    age_sweep(hot, cfg)
    moved_info = archive_sweep(hot, cold, cfg)
    for i in range(11, 14):
        advance_ms(1000)
        seg = make_segment(i, SEG_BYTES, _CLOCK_MS)
        ingest_segment(hot, seg)
    ret_info = enforce_retention(cold, cfg)
    return {
        'moved_count': moved_info['count'],
        'moved_bytes': moved_info['bytes'],
        'dropped_count': ret_info['dropped_count'],
        'retained_cold': ret_info['retained'],
    }

def main():
    cfg = default_config()
    hot = Store('hot')
    cold = Store('cold')
    pipe = run_archive_pipeline(hot, cold, cfg)
    stats = compute_stats(hot, cold)
    print(f"WAL_ARCHIVE_HOT_SEGMENTS={stats['hot_segments']}")
    print(f"WAL_ARCHIVE_HOT_BYTES={stats['hot_bytes']}")
    print(f"WAL_ARCHIVE_COLD_SEGMENTS={stats['cold_segments']}")
    print(f"WAL_ARCHIVE_COLD_BYTES={stats['cold_bytes']}")
    print(f"WAL_ARCHIVE_MOVED_COUNT={pipe['moved_count']}")
    print(f"WAL_ARCHIVE_MOVED_BYTES={pipe['moved_bytes']}")
    print(f"WAL_ARCHIVE_DROPPED_COUNT={pipe['dropped_count']}")
    print(f"WAL_ARCHIVE_RETAINED_COLD={pipe['retained_cold']}")
    print(f"WAL_ARCHIVE_TOTAL_SEGMENTS={stats['total_segments']}")
    print(f"WAL_ARCHIVE_TOTAL_BYTES={stats['total_bytes']}")
    print(f"WAL_ARCHIVE_HOT_OLDEST_AGE_MS={stats['hot_oldest_age_ms']}")
    print(f"WAL_ARCHIVE_COLD_OLDEST_AGE_MS={stats['cold_oldest_age_ms']}")
    print(f"WAL_ARCHIVE_RUN_LOG={drain_log()}")

if __name__ == '__main__':
    main()
