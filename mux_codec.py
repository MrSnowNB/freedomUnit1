#!/usr/bin/env python3
"""
mux_codec.py — MUX Grid Codec for LoRa Mesh Messages
======================================================
v7.0: Dual codebook support (4K legacy + 333K from Kaggle dataset).

4K mode (codebook_size='4k'):
  Word → index lookup into a 4,096-entry frequency-sorted codebook with
  tiered variable-width bit packing.
  Tier 0: Index   0-63   → prefix 0  + 6-bit index =  7 bits
  Tier 1: Index  64-255  → prefix 10 + 8-bit index = 10 bits
  Tier 2: Index 256-4095 → prefix 11 + 12-bit index = 14 bits
  Index 4095 = ESC: emits 14-bit ESC marker + 8-bit length + raw UTF-8 bytes.

333K mode (codebook_size='333k'):
  Word → (row, col) lookup into a 700×700 grid.
  3-byte encoding per word:
    Byte 0: row high 8 bits
    Byte 1: (row low 2 bits << 6) | (col high 6 bits)
    Byte 2: (col low 4 bits << 4) [4 bits reserved]
  ESC: row=1023, col=1023 (all 1s) + 1-byte length + raw UTF-8.

v7.0 additions:
  - codebook_size parameter: '4k' or '333k'
  - encode_keywords(): list of keywords → encoded bytes
  - decode_keywords(): bytes + count → list of keywords
  - ESC fallback preserved for both codebook sizes

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import csv
import logging
import os
import pickle
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Codec IDs for the unified packet header
CODEC_ID_HUFFMAN = 0x01
CODEC_ID_MUX_GRID = 0x02

# ESC index for 4K mode
ESC_INDEX = 4095

# ESC sentinel for 333K mode: (row=1023, col=1023)
# This is outside the 700×700 grid so it can never be a real word address.
ESC_ROW_333K = 1023
ESC_COL_333K = 1023


def encode_grid_3byte(row: int, col: int) -> bytes:
    """
    Encode (row, col) into 3 bytes per v7.0 spec:
      Byte 0: row high 8 bits
      Byte 1: (row low 2 bits << 6) | (col high 6 bits)
      Byte 2: (col low 4 bits << 4)  [4 bits unused]
    """
    b0 = (row >> 2) & 0xFF
    b1 = ((row & 0x03) << 6) | ((col >> 4) & 0x3F)
    b2 = ((col & 0x0F) << 4) & 0xFF
    return bytes([b0, b1, b2])


def decode_grid_3byte(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Decode 3 bytes back to (row, col)."""
    b0, b1, b2 = data[offset], data[offset + 1], data[offset + 2]
    row = (b0 << 2) | ((b1 >> 6) & 0x03)
    col = ((b1 & 0x3F) << 4) | ((b2 >> 4) & 0x0F)
    return row, col


class MuxGridCodec:
    """
    MUX Grid codec: word → grid address → binary encoding.

    v7.0: Supports '4k' and '333k' codebook sizes.

    For '4k': Uses tiered bit packing (7/10/14 bits). Loads from mux_codebook.csv.
    For '333k': Uses fixed 3-byte grid encoding. Loads from codebooks/mux_333k.bin.
    """

    def __init__(self, codebook_csv_path: Optional[str] = None,
                 codebook_size: str = "4k"):
        """
        Args:
            codebook_csv_path: Explicit CSV path (overrides auto-detect). Only for 4K mode.
            codebook_size: '4k' or '333k'. Default '4k' for backward compat.
        """
        self.codebook_size_config = codebook_size

        base = os.path.dirname(os.path.abspath(__file__))

        if codebook_size == "333k":
            self._init_333k(base)
        else:
            self._init_4k(base, codebook_csv_path)

    def _init_333k(self, base: str):
        """Load 333K grid codebook from pre-built .bin file."""
        bin_path = os.path.join(base, "codebooks", "mux_333k.bin")
        if not os.path.exists(bin_path):
            raise FileNotFoundError(
                f"333K MUX codebook not found: {bin_path}\n"
                "Run build_mux_codebook_333k.py first.")

        t0 = time.perf_counter()
        with open(bin_path, "rb") as f:
            data = pickle.load(f)
        load_ms = (time.perf_counter() - t0) * 1000

        self.word_to_addr: dict[str, tuple[int, int]] = data["word_to_addr"]
        self.addr_to_word: dict[tuple[int, int], str] = data["addr_to_word"]
        self.grid_width: int = data["grid_width"]
        self.grid_height: int = data["grid_height"]
        self.codebook_size: int = data["total_words"]

        # Also build the 4K-compatible lookup tables for backward compat
        # in shared interfaces (stats, codebook_coverage, etc.)
        self.word_to_index: dict[str, int] = {}
        self.index_to_word: dict[int, str] = {}

        logger.info("MUX 333K loaded: %d words (%dx%d grid) in %.0f ms",
                     self.codebook_size, self.grid_width, self.grid_height,
                     load_ms)

    def _init_4k(self, base: str, codebook_csv_path: Optional[str]):
        """Load 4K codebook from CSV (legacy path, unchanged)."""
        if codebook_csv_path is None:
            codebook_csv_path = os.path.join(base, "mux_codebook.csv")

        self.word_to_index: dict[str, int] = {}
        self.index_to_word: dict[int, str] = {}
        self.word_to_addr: dict[str, tuple[int, int]] = {}
        self.addr_to_word: dict[tuple[int, int], str] = {}
        self.codebook_size = 0
        self._load_codebook_4k(codebook_csv_path)

    def _load_codebook_4k(self, path: str):
        """Load 4K codebook from CSV."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Codebook not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                idx = int(row["index"])
                word = row["word"]
                if word == "<ESC>":
                    continue  # ESC is a reserved index, not a word
                self.word_to_index[word.lower()] = idx
                self.index_to_word[idx] = word.lower()

        self.codebook_size = len(self.word_to_index)

    # ── 4K Bit-level encoding (unchanged) ──

    @staticmethod
    def _encode_index(idx: int) -> str:
        """Encode a single index using tiered bit packing."""
        if idx < 64:
            return "0" + format(idx, "06b")       # 7 bits
        elif idx < 256:
            return "10" + format(idx, "08b")       # 10 bits
        else:
            return "11" + format(idx, "012b")      # 14 bits

    @staticmethod
    def _encode_esc_word(word: str) -> str:
        """Encode an out-of-codebook word: ESC index + length + raw UTF-8."""
        raw = word.encode("utf-8")
        bits = MuxGridCodec._encode_index(ESC_INDEX)  # 14 bits
        bits += format(len(raw), "08b")                # 8-bit length
        for byte in raw:
            bits += format(byte, "08b")                # raw bytes
        return bits

    # ── Encode (full text) ──

    def encode(self, text: str) -> tuple[bytes, int]:
        """
        Encode text to compressed bytes.

        For 4K mode: tiered bit packing.
        For 333K mode: 3-byte grid encoding per word.

        Returns:
            (payload_bytes, padding_bits) — raw payload without header.
            For 333K mode, padding_bits is always 0 (byte-aligned by design).
        """
        if self.codebook_size_config == "333k":
            return self._encode_333k(text)
        else:
            return self._encode_4k(text)

    def _encode_4k(self, text: str) -> tuple[bytes, int]:
        """4K encode (unchanged from original)."""
        words = text.lower().split()
        bitstream = ""

        for word in words:
            if word in self.word_to_index:
                idx = self.word_to_index[word]
                bitstream += self._encode_index(idx)
            else:
                bitstream += self._encode_esc_word(word)

        # Pad to byte boundary
        padding = (8 - len(bitstream) % 8) % 8
        bitstream += "0" * padding

        payload = (int(bitstream, 2).to_bytes(len(bitstream) // 8,
                                               byteorder="big")
                   if bitstream else b"")
        return payload, padding

    def _encode_333k(self, text: str) -> tuple[bytes, int]:
        """333K encode: 3 bytes per word, ESC for unknown."""
        words = text.lower().split()
        result = bytearray()
        esc_count = 0

        for word in words:
            if word in self.word_to_addr:
                row, col = self.word_to_addr[word]
                result.extend(encode_grid_3byte(row, col))
            else:
                # ESC: sentinel address + length + raw UTF-8
                result.extend(encode_grid_3byte(ESC_ROW_333K, ESC_COL_333K))
                raw = word.encode("utf-8")
                result.append(len(raw) & 0xFF)
                result.extend(raw)
                esc_count += 1
                logger.debug("MUX 333K ESC: '%s'", word)

        if esc_count > 0:
            logger.info("MUX 333K encode: %d/%d ESC sequences",
                         esc_count, len(words))

        return bytes(result), 0  # No padding needed (byte-aligned)

    def encode_packet(self, text: str, seq: int = 0) -> bytes:
        """
        Encode text to a full packet with 3-byte header.

        Byte 0: Codec ID (0x02)
        Byte 1: Sequence number
        Byte 2: Padding bits
        Bytes 3+: Encoded payload
        """
        payload, padding = self.encode(text)
        header = bytes([CODEC_ID_MUX_GRID, seq & 0xFF, padding & 0x07])
        return header + payload

    # ── Decode (full text) ──

    def decode(self, payload: bytes, padding_bits: int) -> str:
        """
        Decode raw payload bytes (without header) back to text.

        For 4K mode: tiered bit unpacking.
        For 333K mode: 3-byte grid decoding.
        """
        if self.codebook_size_config == "333k":
            return self._decode_333k(payload)
        else:
            return self._decode_4k(payload, padding_bits)

    def _decode_4k(self, payload: bytes, padding_bits: int) -> str:
        """4K decode (unchanged from original)."""
        if not payload:
            return ""

        # Convert to bitstream
        bitstream = bin(int.from_bytes(payload, byteorder="big"))[2:]
        bitstream = bitstream.zfill(len(payload) * 8)

        # Trim padding
        if padding_bits > 0:
            bitstream = bitstream[:-padding_bits]

        words = []
        pos = 0

        while pos < len(bitstream):
            remaining = len(bitstream) - pos
            if remaining < 7:
                break  # Not enough bits for even a Tier 0 code

            # Read prefix to determine tier
            if bitstream[pos] == "0":
                # Tier 0: 1-bit prefix + 6-bit index = 7 bits
                if remaining < 7:
                    break
                idx = int(bitstream[pos + 1:pos + 7], 2)
                pos += 7
            elif pos + 1 < len(bitstream) and bitstream[pos + 1] == "0":
                # Tier 1: 2-bit prefix "10" + 8-bit index = 10 bits
                if remaining < 10:
                    break
                idx = int(bitstream[pos + 2:pos + 10], 2)
                pos += 10
            else:
                # Tier 2: 2-bit prefix "11" + 12-bit index = 14 bits
                if remaining < 14:
                    break
                idx = int(bitstream[pos + 2:pos + 14], 2)
                pos += 14

            if idx == ESC_INDEX:
                # ESC: read 8-bit length + raw UTF-8 bytes
                if pos + 8 > len(bitstream):
                    break
                length = int(bitstream[pos:pos + 8], 2)
                pos += 8
                raw_bytes = bytearray()
                for _ in range(length):
                    if pos + 8 > len(bitstream):
                        break
                    raw_bytes.append(int(bitstream[pos:pos + 8], 2))
                    pos += 8
                words.append(raw_bytes.decode("utf-8"))
            elif idx in self.index_to_word:
                words.append(self.index_to_word[idx])
            else:
                words.append(f"<UNK:{idx}>")

        return " ".join(words)

    def _decode_333k(self, payload: bytes) -> str:
        """333K decode: read 3-byte grid addresses sequentially."""
        if not payload:
            return ""

        words = []
        pos = 0

        while pos + 3 <= len(payload):
            row, col = decode_grid_3byte(payload, pos)
            pos += 3

            if row == ESC_ROW_333K and col == ESC_COL_333K:
                # ESC: read length + raw UTF-8
                if pos >= len(payload):
                    break
                length = payload[pos]
                pos += 1
                if pos + length > len(payload):
                    break
                word = payload[pos:pos + length].decode("utf-8")
                pos += length
                words.append(word)
            else:
                word = self.addr_to_word.get((row, col))
                if word:
                    words.append(word)
                else:
                    words.append(f"<UNK:({row},{col})>")

        return " ".join(words)

    def decode_packet(self, packet: bytes) -> tuple[str, int, int, int]:
        """
        Decode a full packet with 3-byte header.

        Returns:
            (decoded_text, codec_id, seq, padding_bits)
        """
        if len(packet) < 3:
            raise ValueError(f"Packet too short: {len(packet)} bytes (need >= 3)")

        codec_id = packet[0]
        seq = packet[1]
        padding = packet[2]
        payload = packet[3:]

        text = self.decode(payload, padding)
        return text, codec_id, seq, padding

    # ── Keyword encode/decode (NEW v7.0) ──

    def encode_keywords(self, keywords: list[str]) -> bytes:
        """
        Encode a list of keywords into bytes.

        For 4K mode: tiered bit packing (tightly packed across boundaries).
        For 333K mode: 3 bytes per keyword (already byte-aligned).
        ESC fallback for unknown words in both modes.

        Args:
            keywords: List of lowercase keyword strings.

        Returns:
            Encoded bytes.
        """
        t0 = time.perf_counter()

        if self.codebook_size_config == "333k":
            result = self._encode_keywords_333k(keywords)
        else:
            result = self._encode_keywords_4k(keywords)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.debug("MUX encode_keywords: %d keywords → %d bytes (%.1f ms)",
                      len(keywords), len(result), elapsed_ms)
        return result

    def _encode_keywords_333k(self, keywords: list[str]) -> bytes:
        """333K keyword encoding: 3 bytes per keyword."""
        result = bytearray()
        esc_count = 0

        for kw in keywords:
            kw_lower = kw.lower().strip()
            if kw_lower in self.word_to_addr:
                row, col = self.word_to_addr[kw_lower]
                result.extend(encode_grid_3byte(row, col))
            else:
                # ESC: sentinel + length + raw
                result.extend(encode_grid_3byte(ESC_ROW_333K, ESC_COL_333K))
                raw = kw_lower.encode("utf-8")
                result.append(len(raw) & 0xFF)
                result.extend(raw)
                esc_count += 1
                logger.debug("MUX 333K keyword ESC: '%s'", kw_lower)

        if esc_count > 0:
            logger.info("MUX 333K encode_keywords: %d/%d ESC",
                         esc_count, len(keywords))

        return bytes(result)

    def _encode_keywords_4k(self, keywords: list[str]) -> bytes:
        """4K keyword encoding: tiered bit packing, tightly packed."""
        bitstream = ""
        esc_count = 0

        for kw in keywords:
            kw_lower = kw.lower().strip()
            if kw_lower in self.word_to_index:
                idx = self.word_to_index[kw_lower]
                bitstream += self._encode_index(idx)
            else:
                bitstream += self._encode_esc_word(kw_lower)
                esc_count += 1

        if esc_count > 0:
            logger.info("MUX 4K encode_keywords: %d/%d ESC",
                         esc_count, len(keywords))

        # Pad to byte boundary
        padding = (8 - len(bitstream) % 8) % 8
        bitstream += "0" * padding

        if not bitstream:
            return b""
        return int(bitstream, 2).to_bytes(len(bitstream) // 8,
                                           byteorder="big")

    def decode_keywords(self, payload: bytes, count: int) -> list[str]:
        """
        Decode exactly 'count' keywords from payload bytes.

        For 4K mode: reads tiered bit-packed codes sequentially.
        For 333K mode: reads 3-byte grid addresses sequentially.

        Args:
            payload: Encoded keyword bytes.
            count: Number of keywords to decode.

        Returns:
            List of decoded keyword strings.
        """
        t0 = time.perf_counter()

        if not payload or count <= 0:
            return []

        if self.codebook_size_config == "333k":
            result = self._decode_keywords_333k(payload, count)
        else:
            result = self._decode_keywords_4k(payload, count)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.debug("MUX decode_keywords: %d keywords in %.1f ms",
                      len(result), elapsed_ms)
        return result

    def _decode_keywords_333k(self, payload: bytes, count: int) -> list[str]:
        """333K keyword decoding: read 3-byte addresses."""
        keywords = []
        pos = 0

        while len(keywords) < count and pos + 3 <= len(payload):
            row, col = decode_grid_3byte(payload, pos)
            pos += 3

            if row == ESC_ROW_333K and col == ESC_COL_333K:
                # ESC: length + raw
                if pos >= len(payload):
                    break
                length = payload[pos]
                pos += 1
                if pos + length > len(payload):
                    break
                word = payload[pos:pos + length].decode("utf-8")
                pos += length
                keywords.append(word)
            else:
                word = self.addr_to_word.get((row, col))
                if word:
                    keywords.append(word)
                else:
                    keywords.append(f"<UNK:({row},{col})>")
                    logger.warning("MUX 333K unknown addr: (%d,%d)", row, col)

        return keywords

    def _decode_keywords_4k(self, payload: bytes, count: int) -> list[str]:
        """4K keyword decoding: read tiered bit-packed codes."""
        bitstream = bin(int.from_bytes(payload, byteorder="big"))[2:]
        bitstream = bitstream.zfill(len(payload) * 8)

        keywords = []
        pos = 0

        while len(keywords) < count and pos < len(bitstream):
            remaining = len(bitstream) - pos
            if remaining < 7:
                break

            if bitstream[pos] == "0":
                if remaining < 7:
                    break
                idx = int(bitstream[pos + 1:pos + 7], 2)
                pos += 7
            elif pos + 1 < len(bitstream) and bitstream[pos + 1] == "0":
                if remaining < 10:
                    break
                idx = int(bitstream[pos + 2:pos + 10], 2)
                pos += 10
            else:
                if remaining < 14:
                    break
                idx = int(bitstream[pos + 2:pos + 14], 2)
                pos += 14

            if idx == ESC_INDEX:
                if pos + 8 > len(bitstream):
                    break
                length = int(bitstream[pos:pos + 8], 2)
                pos += 8
                raw_bytes = bytearray()
                for _ in range(length):
                    if pos + 8 > len(bitstream):
                        break
                    raw_bytes.append(int(bitstream[pos:pos + 8], 2))
                    pos += 8
                keywords.append(raw_bytes.decode("utf-8"))
            elif idx in self.index_to_word:
                keywords.append(self.index_to_word[idx])
            else:
                keywords.append(f"<UNK:{idx}>")

        return keywords

    # ── Analysis ──

    def analyze(self, text: str) -> dict:
        """Analyze compression for a single message."""
        raw_bytes = len(text.encode("utf-8"))
        packet = self.encode_packet(text)
        comp_bytes = len(packet)
        decoded, _, _, _ = self.decode_packet(packet)
        ratio = raw_bytes / comp_bytes if comp_bytes else float("inf")

        return {
            "original": text,
            "decoded": decoded,
            "raw_bytes": raw_bytes,
            "comp_bytes": comp_bytes,
            "header_bytes": 3,
            "payload_bytes": comp_bytes - 3,
            "ratio": ratio,
            "savings_pct": (1 - comp_bytes / raw_bytes) * 100 if raw_bytes else 0,
            "roundtrip": decoded == text.lower(),  # MUX lowercases everything
        }

    def stats(self) -> dict:
        """Codebook statistics."""
        if self.codebook_size_config == "333k":
            return {
                "codebook_size": self.codebook_size,
                "codebook_size_config": self.codebook_size_config,
                "grid_width": self.grid_width,
                "grid_height": self.grid_height,
                "bytes_per_word": 3,
                "spare_slots": (self.grid_width * self.grid_height
                                - self.codebook_size),
            }
        else:
            return {
                "codebook_size": self.codebook_size,
                "codebook_size_config": self.codebook_size_config,
                "tier_0_words": sum(1 for idx in self.word_to_index.values()
                                    if idx < 64),
                "tier_1_words": sum(1 for idx in self.word_to_index.values()
                                    if 64 <= idx < 256),
                "tier_2_words": sum(1 for idx in self.word_to_index.values()
                                    if 256 <= idx < 4095),
                "tier_0_bits": 7,
                "tier_1_bits": 10,
                "tier_2_bits": 14,
            }

    def codebook_coverage(self, text: str) -> dict:
        """Check how many words in the text are in the codebook."""
        words = text.lower().split()
        if self.codebook_size_config == "333k":
            in_cb = sum(1 for w in words if w in self.word_to_addr)
            missing = [w for w in words if w not in self.word_to_addr]
        else:
            in_cb = sum(1 for w in words if w in self.word_to_index)
            missing = [w for w in words if w not in self.word_to_index]
        return {
            "total": len(words),
            "in_cb": in_cb,
            "coverage": in_cb / len(words) * 100 if words else 100,
            "missing": missing,
        }


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
def main():
    import sys
    size = "4k"
    if "--333k" in sys.argv:
        size = "333k"

    codec = MuxGridCodec(codebook_size=size)
    s = codec.stats()

    print("=" * 78)
    print(f"  MUX GRID CODEC v7.0 — CyberMesh / Liberty Mesh")
    print(f"  Codebook: {s['codebook_size_config']} ({s['codebook_size']:,} words)")
    print("=" * 78)

    if size == "333k":
        print(f"  Grid:      {s['grid_width']}×{s['grid_height']} "
              f"({s['grid_width']*s['grid_height']:,} cells)")
        print(f"  Encoding:  {s['bytes_per_word']} bytes/word (fixed)")
        print(f"  Spare:     {s['spare_slots']:,} slots")
    else:
        print(f"  Codebook:  {s['codebook_size']} words")
        print(f"  Tier 0:    {s['tier_0_words']} words (7 bits)")
        print(f"  Tier 1:    {s['tier_1_words']} words (10 bits)")
        print(f"  Tier 2:    {s['tier_2_words']} words (14 bits)")

    # Test messages
    msgs = [
        "ok",
        "SOS",
        "Battery at 89 percent",
        "Node 12 temperature 72 humidity 45",
        "The sensor node is reporting temperature 94 degrees",
        "Alert flood warning for the area",
        "What time is it?",
        "the sensor is online battery at 89 percent signal strong",
    ]

    # For 333K, messages need to be lowercase (pretokenizer handles this)
    if size == "333k":
        msgs = [m.lower() for m in msgs]

    print(f"\n{'=' * 78}")
    print(f"  COMPRESSION BENCHMARKS — 8 Test Messages (full text mode)")
    print(f"{'=' * 78}")
    hdr = (f"  {'#':<3} {'Raw':>4} {'Cmp':>4} {'Hdr':>3} {'Pay':>3} "
           f"{'Ratio':>6} {'Sav%':>5} {'RT'} Message")
    print(hdr)
    print(f"  {'-'*3} {'-'*4} {'-'*4} {'-'*3} {'-'*3} {'-'*6} "
          f"{'-'*5} {'-'*2} {'-'*50}")

    tr = tc = 0
    ok = True
    for i, m in enumerate(msgs, 1):
        r = codec.analyze(m)
        tr += r["raw_bytes"]
        tc += r["comp_bytes"]
        rt = "✓" if r["roundtrip"] else "✗"
        if not r["roundtrip"]:
            ok = False
        dm = m if len(m) <= 55 else m[:52] + "..."
        print(f"  {i:<3} {r['raw_bytes']:>4} {r['comp_bytes']:>4} "
              f"{r['header_bytes']:>3} {r['payload_bytes']:>3} "
              f"{r['ratio']:>6.2f} {r['savings_pct']:>4.0f}% "
              f"{rt}  {dm}")
        if not r["roundtrip"]:
            print(f"      ORIG: '{r['original']}'")
            print(f"      DECD: '{r['decoded']}'")

    ar = tr / tc if tc else 0
    ap = (1 - tc / tr) * 100 if tr else 0
    print(f"\n  {'─' * 76}")
    print(f"  AGGREGATE  {tr:>4} {tc:>4}              {ar:>6.2f} {ap:>4.0f}%")
    print(f"  Roundtrip: {'100% PASS ✓' if ok else 'FAILURES ✗'}")

    # Keyword mode test
    print(f"\n{'=' * 78}")
    print(f"  KEYWORD MODE BENCHMARKS")
    print(f"{'=' * 78}")
    kw_tests = [
        ["flood", "warning", "active", "lawrence", "township", "sensors",
         "operational", "offline"],
        ["sensor", "5", "reads", "2", "feet", "rising"],
        ["emergency", "dispatch", "north", "sector", "3", "casualties"],
        ["battery", "89", "percent", "signal", "strong", "node", "12",
         "online"],
    ]
    kw_ok = True
    for i, kws in enumerate(kw_tests, 1):
        encoded = codec.encode_keywords(kws)
        decoded = codec.decode_keywords(encoded, len(kws))
        rt = decoded == kws
        if not rt:
            kw_ok = False
        bpk = len(encoded) * 8 / len(kws) if kws else 0
        print(f"  [{i}] {len(kws)} keywords → {len(encoded)} bytes "
              f"({bpk:.1f} bits/kw) "
              f"{'✓' if rt else '✗'}")
        if not rt:
            print(f"      IN:  {kws}")
            print(f"      OUT: {decoded}")

    print(f"\n  Keyword roundtrip: {'100% PASS ✓' if kw_ok else 'FAILURES ✗'}")
    print(f"{'=' * 78}")


if __name__ == "__main__":
    main()
