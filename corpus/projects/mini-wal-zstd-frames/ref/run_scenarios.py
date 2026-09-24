#!/usr/bin/env python3
"""Reference implementation of mini-wal-zstd-frames scenario.

Computes the 13 KEY=value lines that the Aura program should emit.
"""

import struct
import zlib

# ---- crc32.aura ----------------------------------------------------------
CRC32_TABLE = [0] * 256
for i in range(256):
    c = i
    for _ in range(8):
        c = (c >> 1) ^ (0xEDB88320 if (c & 1) else 0)
    CRC32_TABLE[i] = c


def crc32_update(crc: int, byte: int) -> int:
    return ((crc >> 8) & 0x00FFFFFF) ^ CRC32_TABLE[(crc ^ byte) & 0xFF]


def crc32_final(crc: int) -> int:
    return crc & 0xFFFFFFFF


def crc32(buf: bytes) -> int:
    crc = 0xFFFFFFFF
    for b in buf:
        crc = crc32_update(crc, b)
    return crc32_final(crc)


# ---- bytebuf.aura --------------------------------------------------------
class ByteBuf:
    def __init__(self):
        self._buf = bytearray()

    def put(self, b):
        self._buf.append(b & 0xFF)

    def get(self):
        return self._buf.pop(0)

    def pos(self):
        return len(self._buf)

    def slice(self, n):
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def length(self):
        return len(self._buf)

    def bytes(self):
        return bytes(self._buf)


# ---- dict.aura -----------------------------------------------------------
class Dict:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.window = bytearray()
        self.id = 0

    def train(self, literals: bytes):
        # rolling window of last `capacity` bytes; pin id from length+hash
        self.window.extend(literals)
        if len(self.window) > self.capacity:
            self.window = self.window[-self.capacity:]
        self.id = (len(self.window) * 2654435761) & 0xFFFF


# ---- codec.aura ----------------------------------------------------------
def codec_compress(d: Dict, raw: bytes) -> bytes:
    """Toy 'mini-zstd': literal-copy + naive back-reference encoder.

    Output: a sequence of tokens. Literal byte: 0x00 <byte>.
    Back-reference: 0x01 <off_lo> <off_hi> <len>.
    """
    out = bytearray()
    i = 0
    win = bytes(d.window)
    while i < len(raw):
        # find longest match in window
        best_off = 0
        best_len = 0
        max_back = min(len(win), i)
        if max_back > 0:
            # search over offsets
            for off in range(1, max_back + 1):
                # extend match
                ln = 0
                while (ln < 255
                       and i + ln < len(raw)
                       and win[-off + (ln % off) if off <= len(win) else 0] == raw[i + ln]):
                    ln += 1
                # Simpler, correct search limited to raw[len] when off small:
                ln = 0
                while ln < 255 and i + ln < len(raw):
                    ref_idx = len(win) - off
                    if ref_idx + (ln % off) >= len(win):
                        break
                    if win[ref_idx + (ln % off)] != raw[i + ln]:
                        break
                    ln += 1
                if ln >= 3 and ln > best_len:
                    best_len = ln
                    best_off = off
        if best_len >= 3:
            out.append(0x01)
            out.append(best_off & 0xFF)
            out.append((best_off >> 8) & 0xFF)
            out.append(best_len & 0xFF)
            i += best_len
        else:
            out.append(0x00)
            out.append(raw[i])
            i += 1
    return bytes(out)


def codec_decompress(d: Dict, framed: bytes) -> bytes:
    """Reverse of codec_compress: not used directly — frame.aura does decode."""
    out = bytearray()
    win = bytes(d.window)
    i = 0
    while i < len(framed):
        tag = framed[i]
        i += 1
        if tag == 0x00:
            out.append(framed[i]); i += 1
        else:
            off = framed[i] | (framed[i + 1] << 8); i += 2
            ln = framed[i]; i += 1
            for k in range(ln):
                if len(win) == 0 or off == 0 or off > len(win):
                    out.append(0)
                else:
                    out.append(win[-off + (k % off)])
    return bytes(out)


_codec_in = 0
_codec_out = 0


def codec_bytes_in():
    return _codec_in


def codec_bytes_out():
    return _codec_out


# ---- frame.aura ----------------------------------------------------------
FRAME_MAGIC = 0xA57E  # arbitrary 2-byte magic
FRAME_VERSION = 1


def frame_encode(d: Dict, payload: bytes) -> bytes:
    """Frame: MAGIC(2) | VER(1) | FLAGS(1) | CRC32(4) | DICT_ID(2) | RAW_LEN(2) | COMP_LEN(2) | PAYLOAD."""
    c = crc32(payload)
    comp = codec_compress(d, payload)
    global _codec_in, _codec_out
    _codec_in += len(payload)
    _codec_out += len(comp)
    header = struct.pack(
        ">HBBIHHH",
        FRAME_MAGIC,
        FRAME_VERSION,
        0x01,  # FLAGS: compressed
        c,
        d.id,
        len(payload),
        len(comp),
    )
    return header + comp


def frame_decode(d: Dict, framed: bytes):
    magic, ver, flags, crc, did, raw_len, comp_len = struct.unpack(
        ">HBBIHHH", framed[:14]
    )
    assert magic == FRAME_MAGIC, "bad magic"
    assert ver == FRAME_VERSION, "bad version"
    comp = framed[14:14 + comp_len]
    raw = codec_decompress(d, comp)
    # Pad/truncate to raw_len for safety
    raw = raw[:raw_len]
    actual = crc32(raw)
    return {"raw": raw, "crc_ok": (actual == crc),
            "crc": crc, "raw_len": raw_len, "comp_len": comp_len}


def frame_crc(framed: bytes) -> int:
    return struct.unpack(">I", framed[4:8])[0]


def frame_raw_len(framed: bytes) -> int:
    return struct.unpack(">H", framed[10:12])[0]


# ---- wal.aura ------------------------------------------------------------
class WAL:
    def __init__(self, block_size=4096, dict_cap=2048):
        self.block_size = block_size
        self.dict = Dict(dict_cap)
        self.buf = ByteBuf()
        self.frames = []           # list of frame-bytes
        self.records = []          # list of (key, value)
        self.raw_bytes = 0         # raw record bytes
        self.stored_bytes = 0      # frame bytes stored
        self._pending = bytearray()

    def append(self, key: str, value: str):
        rec = f"{key}={value}".encode()
        self.records.append((key, value))
        self._pending.extend(rec)
        self.raw_bytes += len(rec)
        if len(self._pending) >= self.block_size:
            self.flush()

    def flush(self):
        if not self._pending:
            return
        # Train dict on the current pending payload so compression can match
        self.dict.train(bytes(self._pending))
        framed = frame_encode(self.dict, bytes(self._pending))
        self.frames.append(framed)
        self.stored_bytes += len(framed)
        self.buf.put(len(framed) & 0xFF)  # tiny length-prefix into bytebuf
        self._pending.clear()

    def read_tail(self):
        if not self.frames:
            return {"partial": True, "raw": b"", "crc_ok": True}
        last = self.frames[-1]
        info = frame_decode(self.dict, last)
        # Partial if the last frame's raw payload is shorter than block_size
        partial = info["raw_len"] < self.block_size
        return {"partial": partial, "raw": info["raw"], "crc_ok": info["crc_ok"]}

    def replay(self):
        out = []
        for fr in self.frames:
            info = frame_decode(self.dict, fr)
            chunk = info["raw"]
            # Records are concatenated "key=value" with no separators in toy version
            out.append(chunk)
        return out


# ---- stats.aura ----------------------------------------------------------
class Stats:
    def __init__(self):
        self.raw = 0
        self.stored = 0

    def on_frame(self, raw, stored):
        self.raw += raw
        self.stored += stored

    def ratio(self):
        if self.raw == 0:
            return 0.0
        return self.stored / self.raw

    def dump(self):
        return f"raw={self.raw} stored={self.stored} ratio={self.ratio():.3f}"


# ---- keys.aura -----------------------------------------------------------
def key_first(wal: WAL):
    return wal.records[0][0] if wal.records else ""


def key_last(wal: WAL):
    return wal.records[-1][0] if wal.records else ""


def key_count(wal: WAL):
    return len(wal.records)


# ---- hex.aura ------------------------------------------------------------
def hex_of_byte(b):
    return f"{b:02x}"


def hex_of_word(n):
    return f"{n:08x}"


# ---- logfmt.aura ---------------------------------------------------------
def logfmt_line(k, v):
    return f"{k}={v}"


def logfmt(kv):
    return " ".join(f"{k}={val}" for k, val in kv)


# ---- main.aura -----------------------------------------------------------
def main():
    wal = WAL(block_size=4096, dict_cap=2048)
    # Pre-train dictionary from ~2 KB of synthetic literals
    seed = b"".join(f"warmup-{i:04d}=".encode() for i in range(50))
    wal.dict.train(seed)

    # Append 42 records, flushing after every 4096 raw bytes (handled inside append)
    for i in range(42):
        key = f"user:{1001 + i}"
        val = f"op=put ts={i}"
        wal.append(key, val)
    # Ensure any remaining pending bytes are flushed (the tail frame)
    wal.flush()

    stats = Stats()
    for fr in wal.frames:
        stats.on_frame(frame_raw_len(fr), len(fr))

    # Read tail
    tail = wal.read_tail()
    tail_partial = tail["partial"]
    crc_ok = tail["crc_ok"]

    # Replay and compare to original concatenated records
    replayed = b"".join(wal.replay())
    expected = b"".join(f"{k}={v}".encode() for k, v in wal.records)
    replay_match = (replayed == expected)

    first_key = key_first(wal)
    last_key = key_last(wal)

    print(f"WAL_MAGIC=0x{FRAME_MAGIC:04x}")
    print(f"WAL_VERSION={FRAME_VERSION}")
    print(f"WAL_FRAMES={len(wal.frames)}")
    print(f"WAL_BLOCK_ALIGN={wal.block_size}")
    print(f"WAL_DICT_SIZE={wal.dict.capacity}")
    print(f"WAL_CRC_OK={'#t' if crc_ok else '#f'}")
    print(f"WAL_TAIL_PARTIAL={'#t' if tail_partial else '#f'}")
    print(f"WAL_BYTES_RAW={wal.raw_bytes}")
    print(f"WAL_BYTES_STORED={wal.stored_bytes}")
    print(f"WAL_RECORDS={len(wal.records)}")
    print(f"WAL_REPLAY_MATCH={'#t' if replay_match else '#f'}")
    print(f"WAL_FIRST_KEY={first_key}")
    print(f"WAL_LAST_KEY={last_key}")


if __name__ == "__main__":
    main()
