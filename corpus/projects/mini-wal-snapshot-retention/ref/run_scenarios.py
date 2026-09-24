#!/usr/bin/env python3
"""
Python reference for the Aura multi-file project: mini-wal-snapshot-retention.

This script implements the same in-memory semantics described in GOAL.md
and prints the 16 KEY=value lines that the verifier expects.
"""

import sys
from dataclasses import dataclass, field
from typing import List, Optional


SEG_SIZE = 10  # records per segment
TOTAL_APPENDS = 50


# ---------------------------------------------------------------------------
# wal_segment.aura
# ---------------------------------------------------------------------------
@dataclass
class Segment:
    records: List = field(default_factory=list)

    @property
    def high(self) -> int:
        # High-water LSN is the LSN of the last record in the segment.
        # Empty segments are never produced by append, so records is non-empty
        # for any segment returned by wal-segments.
        return self.records[-1]["lsn"]

    def size(self) -> int:
        # We treat "bytes" as record count * SEG_SIZE for simplicity; the
        # reference project uses a constant SEG_SIZE per record.
        return SEG_SIZE * len(self.records)

    def records_list(self):
        return list(self.records)


# ---------------------------------------------------------------------------
# wal_log.aura
# ---------------------------------------------------------------------------
class WAL:
    def __init__(self):
        self.records: List = []
        self.segments: List[Segment] = []

    def append(self, lsn: int, payload):
        rec = {"lsn": lsn, "payload": payload}
        self.records.append(rec)
        seg_index = lsn // SEG_SIZE
        # Grow segments list as needed.
        while len(self.segments) <= seg_index:
            self.segments.append(Segment())
        self.segments[seg_index].records.append(rec)

    @property
    def lsn(self) -> int:
        # The next LSN to be assigned is len(records) because LSNs start at 0.
        # "Last LSN" the verifier expects is len(records)-1, so we expose
        # last-lsn as len(records)-1 via a helper.
        return len(self.records) - 1 if self.records else -1

    def next_lsn(self) -> int:
        return len(self.records)

    def segments_list(self) -> List[Segment]:
        return list(self.segments)

    def record_count(self) -> int:
        return len(self.records)


# ---------------------------------------------------------------------------
# wal_snapshot.aura
# ---------------------------------------------------------------------------
@dataclass
class Snapshot:
    lsn_at: int
    snap_id: int
    _released: bool = False

    def snapshot_lsn(self) -> int:
        return self.lsn_at

    def snapshot_id(self) -> int:
        return self.snap_id

    def snapshot_live(self) -> bool:
        return not self._released

    def snapshot_release(self):
        self._released = True


# ---------------------------------------------------------------------------
# wal_manager.aura
# ---------------------------------------------------------------------------
class Manager:
    def __init__(self):
        self.wal = WAL()
        self.snapshots: List[Snapshot] = []
        self._next_snap_id = 0

    # --- append ---
    def manager_append(self, payload):
        lsn = self.wal.next_lsn()
        self.wal.append(lsn, payload)
        return lsn

    def manager_lsn(self) -> int:
        return self.wal.lsn

    def manager_segments(self) -> List[Segment]:
        return self.wal.segments_list()

    def manager_record_count(self) -> int:
        return self.wal.record_count()

    def manager_snapshots(self) -> List[Snapshot]:
        return list(self.snapshots)

    # --- snapshots ---
    def manager_take_snapshot(self, lsn: int) -> Snapshot:
        snap = Snapshot(lsn_at=lsn, snap_id=self._next_snap_id)
        self._next_snap_id += 1
        self.snapshots.append(snap)
        return snap

    # --- retention ---
    def manager_prune_lsn(self) -> int:
        # The prune LSN is the minimum LSN across all live snapshots.
        # With no live snapshots, it is 0 (nothing strictly below 0).
        live_lsns = [s.lsn_at for s in self.snapshots if s.snapshot_live()]
        if not live_lsns:
            return 0
        return min(live_lsns)

    def manager_prune_segments(self) -> int:
        prune_lsn = self.manager_prune_lsn()
        # Segments whose high-water is strictly below prune_lsn are reclaimable.
        count = 0
        for seg in self.manager_segments():
            if seg.high < prune_lsn:
                count += 1
        return count

    def manager_reclaim_bytes(self) -> int:
        prune_lsn = self.manager_prune_lsn()
        total = 0
        for seg in self.manager_segments():
            if seg.high < prune_lsn:
                total += seg.size()
        return total


# ---------------------------------------------------------------------------
# wal_replay.aura
# ---------------------------------------------------------------------------
class Replay:
    def __init__(self, last_lsn: int, snap_lsn: int):
        self._last_lsn = last_lsn
        self._snap_lsn = snap_lsn

    def replay_last_lsn(self) -> int:
        return self._last_lsn

    def replay_snapshot_lsn(self) -> int:
        return self._snap_lsn


def replay_build(mgr: Manager, snap_lsn: int) -> Replay:
    # Re-derive state from the WAL alone.
    last = mgr.manager_lsn()
    return Replay(last_lsn=last, snap_lsn=snap_lsn)


# ---------------------------------------------------------------------------
# Scenario driver (wal_main.aura)
# ---------------------------------------------------------------------------
def main():
    out_lines = []

    # 1. Create manager.
    mgr = Manager()

    # 2. Append 50 records.
    for i in range(TOTAL_APPENDS):
        mgr.manager_append(f"rec-{i}")

    # 3. Segment highs (first 5 segments).
    segments = mgr.manager_segments()
    for k in range(5):
        out_lines.append(f"SEG{k}_HI={segments[k].high}")

    # Counts and last LSN.
    out_lines.append(f"APPEND_COUNT={mgr.manager_record_count()}")
    out_lines.append(f"LAST_LSN={mgr.manager_lsn()}")

    # 4. Take snapshot at LSN 9.
    snap = mgr.manager_take_snapshot(9)
    out_lines.append(f"SNAPSHOT_LSN={snap.snapshot_lsn()}")
    out_lines.append(f"SNAPSHOT_COUNT={len(mgr.manager_snapshots())}")

    # 5. Release the snapshot and report liveness.
    snap.snapshot_release()
    live_after = sum(1 for s in mgr.manager_snapshots() if s.snapshot_live())
    out_lines.append(f"AFTER_RELEASE_LIVE={live_after}")

    # 6. Retention.
    prune_lsn = mgr.manager_prune_lsn()
    prune_segs = mgr.manager_prune_segments()
    reclaim = mgr.manager_reclaim_bytes()
    out_lines.append(f"PRUNE_LSN={prune_lsn}")
    out_lines.append(f"PRUNE_SEGMENTS={prune_segs}")
    out_lines.append(f"RECLAIM_BYTES={reclaim}")

    # 7. Replay view. The snapshot LSN of the replay is the LSN at which
    #    a snapshot was originally taken (here, 9).
    replay = replay_build(mgr, snap_lsn=snap.snapshot_lsn())
    out_lines.append(f"SEG0_HI_REPLAY={segments[0].high}")
    out_lines.append(f"SNAPSHOT_LSN_REPLAY={replay.replay_snapshot_lsn()}")
    out_lines.append(f"LAST_LSN_REPLAY={replay.replay_last_lsn()}")

    # Emit exactly the 16 lines.
    for line in out_lines:
        sys.stdout.write(line + "\n")


if __name__ == "__main__":
    main()
