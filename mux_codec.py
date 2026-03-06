#!/usr/bin/env python3
"""
mux_codec.py — MUX Grid Codec for LoRa Mesh Messages
======================================================
v7.1: Tri-codebook support (4K legacy + 333K 2D grid + Cube 96³ 3D).

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

Cube96 mode (codebook_size='cube96'):
  Word → (x, y, z) lookup in a 96³ cube via SHA-256 hash + linear probe.
  3-byte encoding per word (byte-aligned, MCU-friendly):
    Byte 0: [F0 | x6..x0]   F0 = namespace  (0=static, 1=meshlex)
    Byte 1: [F1 | y6..y0]   F1 = hyperedge  (reserved, always 0)
    Byte 2: [F2 | z6..z0]   F2 = capitalized (0=lower, 1=cap)
  ESC sentinel: 0xFF 0xFF 0xFF + 1-byte length + raw UTF-8.
  SHARED coordinate space: static and MeshLex words in same cube.
  Inner packet format: [word_count:1B][def_count:1B][defs...][body...]

v7.0 additions:
  - codebook_size parameter: '4k', '333k', or 'cube96'
  - encode_keywords(): list of keywords → encoded bytes
  - decode_keywords(): bytes + count → list of keywords
  - ESC fallback preserved for all codebook sizes

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import csv
import hashlib
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

# ═══════════════════════════════════════════════════════════════════════════
# Cube96 Constants
# ═══════════════════════════════════════════════════════════════════════════

CUBE_SIZE = 96
MAX_CUBE_COORD = CUBE_SIZE - 1  # 95

# ESC sentinel for cube96: 0xFF 0xFF 0xFF → x=127, y=127, z=127 (outside 0-95)
ESC_CUBE_BYTE = 0xFF


# ═══════════════════════════════════════════════════════════════════════════
# 333K 2D Grid Pack/Unpack (unchanged)
# ═══════════════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════════════
# Cube96 3D Pack/Unpack (FROZEN — from spec, direct byte ops only)
# ═══════════════════════════════════════════════════════════════════════════

def pack_cube96(x: int, y: int, z: int,
                f_namespace: int = 0, f_hyperedge: int = 0,
                f_capitalized: int = 0) -> bytes:
    """
    Pack (x, y, z) + 3 flag bits into 3 bytes. One flag per byte high bit.
    Zero cross-byte operations. MCU-friendly.

    Byte 0: [F0 | x6..x0]   F0 = namespace
    Byte 1: [F1 | y6..y0]   F1 = hyperedge (reserved)
    Byte 2: [F2 | z6..z0]   F2 = capitalized
    """
    return bytes([(f_namespace << 7) | (x & 0x7F),
                  (f_hyperedge << 7) | (y & 0x7F),
                  (f_capitalized << 7) | (z & 0x7F)])


def unpack_cube96(data: bytes, offset: int = 0) -> dict:
    """
    Unpack 3 bytes into (x, y, z) + 3 flag bits. Zero cross-byte operations.

    Returns dict with keys: x, y, z, f_namespace, f_hyperedge, f_capitalized
    """
    b0 = data[offset]
    b1 = data[offset + 1]
    b2 = data[offset + 2]
    return {
        'x': b0 & 0x7F,
        'y': b1 & 0x7F,
        'z': b2 & 0x7F,
        'f_namespace': b0 >> 7,
        'f_hyperedge': b1 >> 7,
        'f_capitalized': b2 >> 7,
    }


def is_esc_cube96(data: bytes, offset: int = 0) -> bool:
    """Check if 3 bytes at offset are the ESC sentinel 0xFF 0xFF 0xFF."""
    return (data[offset] == ESC_CUBE_BYTE and
            data[offset + 1] == ESC_CUBE_BYTE and
            data[offset + 2] == ESC_CUBE_BYTE)


def cube96_hash_coords(word: str) -> tuple[int, int, int]:
    """Deterministic initial coordinates via SHA-256 hash of lowercase word."""
    h = hashlib.sha256(word.encode('utf-8')).digest()
    return (h[0] % CUBE_SIZE, h[1] % CUBE_SIZE, h[2] % CUBE_SIZE)


def cube96_probe_place(word: str, occupied: dict) -> tuple[int, int, int]:
    """
    Place word in cube via SHA-256 hash + linear probe Z→Y→X.
    Three-counter approach per spec.

    Args:
        word: lowercased word string
        occupied: dict of (x,y,z) → word (shared coordinate space)

    Returns:
        (x, y, z) tuple — the assigned coordinates
    """
    x, y, z = cube96_hash_coords(word)

    z_attempts = 0
    y_attempts = 0

    while (x, y, z) in occupied:
        z = (z + 1) % CUBE_SIZE
        z_attempts += 1
        if z_attempts >= CUBE_SIZE:
            z_attempts = 0
            y = (y + 1) % CUBE_SIZE
            y_attempts += 1
            if y_attempts >= CUBE_SIZE:
                y_attempts = 0
                x = (x + 1) % CUBE_SIZE

    return (x, y, z)


class MuxGridCodec:
    """
    MUX Grid codec: word → grid address → binary encoding.

    v7.1: Supports '4k', '333k', and 'cube96' codebook sizes.

    For '4k': Uses tiered bit packing (7/10/14 bits). Loads from mux_codebook.csv.
    For '333k': Uses fixed 3-byte 2D grid encoding. Loads from codebooks/mux_333k.bin.
    For 'cube96': Uses fixed 3-byte 3D cube encoding with flag bits.
                  Loads from codebooks/mux_cube96.bin.
    """

    def __init__(self, codebook_csv_path: Optional[str] = None,
                 codebook_size: str = "4k"):
        """
        Args:
            codebook_csv_path: Explicit CSV path (overrides auto-detect). Only for 4K mode.
            codebook_size: '4k', '333k', or 'cube96'. Default '4k' for backward compat.
        """
        self.codebook_size_config = codebook_size

        base = os.path.dirname(os.path.abspath(__file__))

        if codebook_size == "cube96":
            self._init_cube96(base)
        elif codebook_size == "333k":
            self._init_333k(base)
        else:
            self._init_4k(base, codebook_csv_path)

    # ── Cube96 init ──

    def _init_cube96(self, base: str):
        """Load Cube 96³ codebook from pre-built .bin file."""
        bin_path = os.path.join(base, "codebooks", "mux_cube96.bin")
        if not os.path.exists(bin_path):
            raise FileNotFoundError(
                f"Cube96 MUX codebook not found: {bin_path}\n"
                "Run build_mux_cube96.py first.")

        t0 = time.perf_counter()
        with open(bin_path, "rb") as f:
            data = pickle.load(f)
        load_ms = (time.perf_counter() - t0) * 1000

        # Static codebook (from Kaggle unigram frequency data)
        self.word_to_xyz: dict[str, tuple[int, int, int]] = data["word_to_xyz"]
        self.xyz_to_word: dict[tuple[int, int, int], str] = data["xyz_to_word"]
        self.cube_size: int = data["cube_size"]
        self.codebook_size: int = data["total_words"]

        # MeshLex dynamic dictionaries — SEPARATE from static, SHARED coordinate space
        self.meshlex_word_to_xyz: dict[str, tuple[int, int, int]] = {}
        self.meshlex_xyz_to_word: dict[tuple[int, int, int], str] = {}

        # Empty 4K-compatible lookup tables for backward compat in shared interfaces
        self.word_to_index: dict[str, int] = {}
        self.index_to_word: dict[int, str] = {}
        self.word_to_addr: dict[str, tuple[int, int]] = {}
        self.addr_to_word: dict[tuple[int, int], str] = {}

        logger.info("MUX Cube96 loaded: %d words (%d³ cube) in %.0f ms",
                     self.codebook_size, self.cube_size, load_ms)

    # ── 333K init (unchanged) ──

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

    # ── 4K init (unchanged) ──

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

    # ══════════════════════════════════════════════════════════════════════
    # 4K Bit-level encoding (unchanged)
    # ══════════════════════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════════════════════
    # Cube96 MeshLex Helpers
    # ══════════════════════════════════════════════════════════════════════

    def _get_all_occupied_cube96(self) -> dict:
        """
        Return combined occupied map for SHARED coordinate space.
        Static + MeshLex words share the same cube.
        """
        occupied = dict(self.xyz_to_word)
        occupied.update(self.meshlex_xyz_to_word)
        return occupied

    def _meshlex_place_oov(self, word_lower: str) -> tuple[int, int, int]:
        """
        Place an OOV word into MeshLex namespace via SHA-256 hash + probe.
        Shared coordinate space: probes against both static and MeshLex.

        Returns:
            (x, y, z) — assigned coordinates
        """
        occupied = self._get_all_occupied_cube96()
        xyz = cube96_probe_place(word_lower, occupied)
        self.meshlex_word_to_xyz[word_lower] = xyz
        self.meshlex_xyz_to_word[xyz] = word_lower
        logger.info("MeshLex OOV placed: '%s' → (%d,%d,%d)",
                     word_lower, xyz[0], xyz[1], xyz[2])
        return xyz

    # ══════════════════════════════════════════════════════════════════════
    # Cube96 Inline MeshLex Definition Encoding
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def encode_meshlex_def(word_lower: str, x: int, y: int, z: int) -> bytes:
        """
        Encode a single inline MeshLex definition.
        Format: [len:1B][word_utf8:len bytes][packed_coord:3B]

        The packed coord uses F0=1 (meshlex), F1=0, F2=0.
        """
        raw = word_lower.encode("utf-8")
        result = bytearray()
        result.append(len(raw) & 0xFF)
        result.extend(raw)
        result.extend(pack_cube96(x, y, z, f_namespace=1, f_hyperedge=0,
                                  f_capitalized=0))
        return bytes(result)

    @staticmethod
    def decode_meshlex_def(data: bytes, offset: int) -> tuple[str, tuple[int, int, int], int]:
        """
        Decode a single inline MeshLex definition.

        Returns:
            (word, (x, y, z), new_offset)
        """
        word_len = data[offset]
        offset += 1
        word = data[offset:offset + word_len].decode("utf-8")
        offset += word_len
        info = unpack_cube96(data, offset)
        offset += 3
        return (word, (info['x'], info['y'], info['z']), offset)

    # ══════════════════════════════════════════════════════════════════════
    # Encode (full text)
    # ══════════════════════════════════════════════════════════════════════

    def encode(self, text: str) -> tuple[bytes, int]:
        """
        Encode text to compressed bytes.

        For 4K mode: tiered bit packing.
        For 333K mode: 3-byte grid encoding per word.
        For cube96 mode: 3-byte cube encoding with inner format header.

        Returns:
            (payload_bytes, padding_bits) — raw payload without transport header.
            For 333K and cube96 modes, padding_bits is always 0 (byte-aligned).
        """
        if self.codebook_size_config == "cube96":
            return self._encode_cube96(text)
        elif self.codebook_size_config == "333k":
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
                logger.info("MUX 333K ESC: '%s' (not in codebook)", word)

        if esc_count > 0:
            logger.info("MUX 333K encode: %d/%d ESC sequences",
                         esc_count, len(words))

        return bytes(result), 0  # No padding needed (byte-aligned)

    def _encode_cube96(self, text: str) -> tuple[bytes, int]:
        """
        Cube96 encode: 3 bytes per word with flag bits.
        Produces inner format: [word_count:1B][def_count:1B][defs...][body...]

        Static words → F0=0, MeshLex words → F0=1.
        Capitalization → F2=1 if original word starts uppercase.
        F1 always 0 (reserved).
        OOV words → SHA-256 hash + probe into MeshLex, with inline def.
        ESC fallback → 0xFF 0xFF 0xFF + length + raw UTF-8.
        """
        raw_words = text.split()
        body = bytearray()
        inline_defs = bytearray()
        def_count = 0
        esc_count = 0

        for original_word in raw_words:
            word_lower = original_word.lower()
            f_capitalized = 1 if original_word and original_word[0].isupper() else 0
            f_hyperedge = 0  # reserved

            # Check static codebook first
            if word_lower in self.word_to_xyz:
                x, y, z = self.word_to_xyz[word_lower]
                body.extend(pack_cube96(x, y, z,
                                        f_namespace=0,
                                        f_hyperedge=f_hyperedge,
                                        f_capitalized=f_capitalized))

            # Check MeshLex dynamic dict
            elif word_lower in self.meshlex_word_to_xyz:
                x, y, z = self.meshlex_word_to_xyz[word_lower]
                body.extend(pack_cube96(x, y, z,
                                        f_namespace=1,
                                        f_hyperedge=f_hyperedge,
                                        f_capitalized=f_capitalized))

            # OOV — try to place in MeshLex via hash + probe
            elif len(word_lower.encode("utf-8")) <= 31:
                # Place in MeshLex
                x, y, z = self._meshlex_place_oov(word_lower)
                # Add inline definition
                inline_defs.extend(self.encode_meshlex_def(word_lower, x, y, z))
                def_count += 1
                # Encode body reference
                body.extend(pack_cube96(x, y, z,
                                        f_namespace=1,
                                        f_hyperedge=f_hyperedge,
                                        f_capitalized=f_capitalized))

            else:
                # ESC fallback for extremely long words
                body.extend(bytes([ESC_CUBE_BYTE, ESC_CUBE_BYTE, ESC_CUBE_BYTE]))
                raw = word_lower.encode("utf-8")
                body.append(len(raw) & 0xFF)
                body.extend(raw)
                esc_count += 1
                logger.info("MUX Cube96 ESC: '%s' (too long for MeshLex)", word_lower)

        if esc_count > 0:
            logger.info("MUX Cube96 encode: %d/%d ESC sequences",
                         esc_count, len(raw_words))

        # Assemble inner format: [word_count][def_count][defs...][body...]
        word_count = len(raw_words)
        result = bytearray()
        result.append(word_count & 0xFF)
        result.append(def_count & 0xFF)
        result.extend(inline_defs)
        result.extend(body)

        logger.debug("MUX Cube96 encode: %d words, %d defs, %d body bytes, %d total",
                      word_count, def_count, len(body), len(result))

        return bytes(result), 0  # byte-aligned

    def encode_packet(self, text: str, seq: int = 0) -> bytes:
        """
        Encode text to a full packet with 3-byte header.

        Byte 0: Codec ID (0x02)
        Byte 1: Sequence number
        Byte 2: Padding bits
        Bytes 3+: Encoded payload

        NOTE: For cube96 mode, use packet.py's CyberMeshPacket.encode()
        instead. This method is kept for 4K/333K backward compatibility.
        """
        payload, padding = self.encode(text)
        header = bytes([CODEC_ID_MUX_GRID, seq & 0xFF, padding & 0x07])
        return header + payload

    # ══════════════════════════════════════════════════════════════════════
    # Decode (full text)
    # ══════════════════════════════════════════════════════════════════════

    def decode(self, payload: bytes, padding_bits: int) -> str:
        """
        Decode raw payload bytes (without header) back to text.

        For 4K mode: tiered bit unpacking.
        For 333K mode: 3-byte grid decoding.
        For cube96 mode: 3-byte cube decoding with inner format header.
        """
        if self.codebook_size_config == "cube96":
            return self._decode_cube96(payload)
        elif self.codebook_size_config == "333k":
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

    def _decode_cube96(self, payload: bytes) -> str:
        """
        Cube96 decode: parse inner format header, load inline defs, decode body.
        Inner format: [word_count:1B][def_count:1B][defs...][body...]
        """
        if not payload or len(payload) < 2:
            return ""

        pos = 0

        # Read inner header
        word_count = payload[pos]
        pos += 1
        def_count = payload[pos]
        pos += 1

        # Read inline MeshLex definitions and register them
        for _ in range(def_count):
            if pos >= len(payload):
                break
            word, xyz, pos = self.decode_meshlex_def(payload, pos)
            # Register in MeshLex dicts (shared coordinate space)
            if word not in self.meshlex_word_to_xyz:
                self.meshlex_word_to_xyz[word] = xyz
                self.meshlex_xyz_to_word[xyz] = word
                logger.debug("MeshLex def loaded: '%s' → (%d,%d,%d)",
                             word, xyz[0], xyz[1], xyz[2])

        # Decode body words
        words = []
        decoded_count = 0

        while decoded_count < word_count and pos + 3 <= len(payload):
            # Check for ESC sentinel
            if is_esc_cube96(payload, pos):
                pos += 3
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
                decoded_count += 1
                continue

            # Unpack coordinate + flags
            info = unpack_cube96(payload, pos)
            pos += 3

            x, y, z = info['x'], info['y'], info['z']
            f_namespace = info['f_namespace']
            f_capitalized = info['f_capitalized']

            # Lookup word
            if f_namespace == 0:
                # Static codebook
                word = self.xyz_to_word.get((x, y, z))
            else:
                # MeshLex dynamic
                word = self.meshlex_xyz_to_word.get((x, y, z))

            if word is None:
                word = f"<UNK:({x},{y},{z})>"
                logger.warning("MUX Cube96 unknown addr: (%d,%d,%d) ns=%d",
                               x, y, z, f_namespace)

            # Restore capitalization
            if f_capitalized == 1 and word and not word.startswith("<"):
                word = word[0].upper() + word[1:] if len(word) > 1 else word.upper()

            words.append(word)
            decoded_count += 1

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

    # ══════════════════════════════════════════════════════════════════════
    # Keyword encode/decode (v7.0)
    # ══════════════════════════════════════════════════════════════════════

    def encode_keywords(self, keywords: list[str]) -> bytes:
        """
        Encode a list of keywords into bytes.

        For 4K mode: tiered bit packing (tightly packed across boundaries).
        For 333K mode: 3 bytes per keyword (already byte-aligned).
        For cube96 mode: 3 bytes per keyword with flag bits.
        ESC fallback for unknown words in all modes.

        Args:
            keywords: List of keyword strings.

        Returns:
            Encoded bytes.
        """
        t0 = time.perf_counter()

        if self.codebook_size_config == "cube96":
            result = self._encode_keywords_cube96(keywords)
        elif self.codebook_size_config == "333k":
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
                logger.info("MUX 333K keyword ESC: '%s' (not in codebook)", kw_lower)

        if esc_count > 0:
            logger.info("MUX 333K encode_keywords: %d/%d ESC",
                         esc_count, len(keywords))

        return bytes(result)

    def _encode_keywords_cube96(self, keywords: list[str]) -> bytes:
        """Cube96 keyword encoding: 3 bytes per keyword with flag bits."""
        result = bytearray()
        esc_count = 0

        for kw in keywords:
            kw_lower = kw.lower().strip()
            f_capitalized = 1 if kw.strip() and kw.strip()[0].isupper() else 0

            if kw_lower in self.word_to_xyz:
                x, y, z = self.word_to_xyz[kw_lower]
                result.extend(pack_cube96(x, y, z,
                                          f_namespace=0, f_hyperedge=0,
                                          f_capitalized=f_capitalized))
            elif kw_lower in self.meshlex_word_to_xyz:
                x, y, z = self.meshlex_word_to_xyz[kw_lower]
                result.extend(pack_cube96(x, y, z,
                                          f_namespace=1, f_hyperedge=0,
                                          f_capitalized=f_capitalized))
            else:
                # ESC sentinel + length + raw UTF-8
                result.extend(bytes([ESC_CUBE_BYTE, ESC_CUBE_BYTE, ESC_CUBE_BYTE]))
                raw = kw_lower.encode("utf-8")
                result.append(len(raw) & 0xFF)
                result.extend(raw)
                esc_count += 1
                logger.info("MUX Cube96 keyword ESC: '%s'", kw_lower)

        if esc_count > 0:
            logger.info("MUX Cube96 encode_keywords: %d/%d ESC",
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
        For cube96 mode: reads 3-byte cube coordinates sequentially.

        Args:
            payload: Encoded keyword bytes.
            count: Number of keywords to decode.

        Returns:
            List of decoded keyword strings.
        """
        t0 = time.perf_counter()

        if not payload or count <= 0:
            return []

        if self.codebook_size_config == "cube96":
            result = self._decode_keywords_cube96(payload, count)
        elif self.codebook_size_config == "333k":
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

    def _decode_keywords_cube96(self, payload: bytes, count: int) -> list[str]:
        """Cube96 keyword decoding: read 3-byte cube coordinates."""
        keywords = []
        pos = 0

        while len(keywords) < count and pos + 3 <= len(payload):
            # Check for ESC sentinel
            if is_esc_cube96(payload, pos):
                pos += 3
                if pos >= len(payload):
                    break
                length = payload[pos]
                pos += 1
                if pos + length > len(payload):
                    break
                word = payload[pos:pos + length].decode("utf-8")
                pos += length
                keywords.append(word)
                continue

            info = unpack_cube96(payload, pos)
            pos += 3

            x, y, z = info['x'], info['y'], info['z']
            f_namespace = info['f_namespace']
            f_capitalized = info['f_capitalized']

            if f_namespace == 0:
                word = self.xyz_to_word.get((x, y, z))
            else:
                word = self.meshlex_xyz_to_word.get((x, y, z))

            if word is None:
                word = f"<UNK:({x},{y},{z})>"
                logger.warning("MUX Cube96 keyword unknown addr: (%d,%d,%d) ns=%d",
                               x, y, z, f_namespace)

            # Restore capitalization
            if f_capitalized == 1 and word and not word.startswith("<"):
                word = word[0].upper() + word[1:] if len(word) > 1 else word.upper()

            keywords.append(word)

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

    # ══════════════════════════════════════════════════════════════════════
    # Analysis
    # ══════════════════════════════════════════════════════════════════════

    def analyze(self, text: str) -> dict:
        """Analyze compression for a single message."""
        raw_bytes = len(text.encode("utf-8"))

        if self.codebook_size_config == "cube96":
            # For cube96, encode returns inner format payload
            payload, _ = self.encode(text)
            comp_bytes = len(payload)
            # Decode to verify roundtrip
            decoded = self.decode(payload, 0)
        else:
            packet = self.encode_packet(text)
            comp_bytes = len(packet)
            decoded, _, _, _ = self.decode_packet(packet)

        ratio = raw_bytes / comp_bytes if comp_bytes else float("inf")

        return {
            "original": text,
            "decoded": decoded,
            "raw_bytes": raw_bytes,
            "comp_bytes": comp_bytes,
            "ratio": ratio,
            "savings_pct": (1 - comp_bytes / raw_bytes) * 100 if raw_bytes else 0,
            "roundtrip": decoded == text.lower(),  # MUX lowercases everything
        }

    def stats(self) -> dict:
        """Codebook statistics."""
        if self.codebook_size_config == "cube96":
            return {
                "codebook_size": self.codebook_size,
                "codebook_size_config": self.codebook_size_config,
                "cube_dim": self.cube_size,
                "total_capacity": self.cube_size ** 3,
                "bytes_per_word": 3,
                "spare_slots": self.cube_size ** 3 - self.codebook_size,
                "meshlex_words": len(self.meshlex_word_to_xyz),
                "utilization_pct": round(
                    self.codebook_size / (self.cube_size ** 3) * 100, 1),
            }
        elif self.codebook_size_config == "333k":
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
        if self.codebook_size_config == "cube96":
            in_cb = sum(1 for w in words if w in self.word_to_xyz)
            missing = [w for w in words if w not in self.word_to_xyz]
        elif self.codebook_size_config == "333k":
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
    elif "--cube96" in sys.argv:
        size = "cube96"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    codec = MuxGridCodec(codebook_size=size)
    s = codec.stats()

    print("=" * 78)
    print(f"  MUX GRID CODEC v7.1 — CyberMesh / Liberty Mesh")
    print(f"  Codebook: {s['codebook_size_config']} ({s['codebook_size']:,} words)")
    print("=" * 78)

    if size == "cube96":
        print(f"  Cube:      {s['cube_dim']}³ = {s['total_capacity']:,} cells")
        print(f"  Encoding:  {s['bytes_per_word']} bytes/word (fixed)")
        print(f"  Spare:     {s['spare_slots']:,} slots")
        print(f"  Util:      {s['utilization_pct']}%")
        print(f"  MeshLex:   {s['meshlex_words']} dynamic words")
    elif size == "333k":
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

    # For 333K/cube96, messages need to be lowercase (pretokenizer handles this)
    if size in ("333k", "cube96"):
        msgs = [m.lower() for m in msgs]

    print(f"\n{'=' * 78}")
    print(f"  COMPRESSION BENCHMARKS — 8 Test Messages (full text mode)")
    print(f"{'=' * 78}")

    if size == "cube96":
        hdr = (f"  {'#':<3} {'Raw':>4} {'Cmp':>4} "
               f"{'Ratio':>6} {'Sav%':>5} {'RT'} Message")
        print(hdr)
        print(f"  {'-'*3} {'-'*4} {'-'*4} {'-'*6} "
              f"{'-'*5} {'-'*2} {'-'*50}")
    else:
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

        if size == "cube96":
            print(f"  {i:<3} {r['raw_bytes']:>4} {r['comp_bytes']:>4} "
                  f"{r['ratio']:>6.2f} {r['savings_pct']:>4.0f}% "
                  f"{rt}  {dm}")
        else:
            print(f"  {i:<3} {r['raw_bytes']:>4} {r['comp_bytes']:>4} "
                  f"{r.get('header_bytes', 0):>3} {r.get('payload_bytes', 0):>3} "
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

    # Cube96 extra tests
    if size == "cube96":
        print(f"\n{'=' * 78}")
        print(f"  CUBE96 SPECIFIC TESTS")
        print(f"{'=' * 78}")
        cube_ok = True

        # Test 1: Capitalization flag
        print("\n  [C1] Capitalization flag test")
        test_word = "the"
        if test_word in codec.word_to_xyz:
            x, y, z = codec.word_to_xyz[test_word]
            packed_lower = pack_cube96(x, y, z, f_namespace=0, f_hyperedge=0,
                                       f_capitalized=0)
            packed_cap = pack_cube96(x, y, z, f_namespace=0, f_hyperedge=0,
                                     f_capitalized=1)
            info_lo = unpack_cube96(packed_lower)
            info_hi = unpack_cube96(packed_cap)
            cap_ok = (info_lo['x'] == info_hi['x'] and
                      info_lo['y'] == info_hi['y'] and
                      info_lo['z'] == info_hi['z'] and
                      info_lo['f_capitalized'] == 0 and
                      info_hi['f_capitalized'] == 1)
            print(f"      '{test_word}' lower: F2=0, cap: F2=1, "
                  f"same (x,y,z)=({x},{y},{z}): {'✓' if cap_ok else '✗'}")
            if not cap_ok:
                cube_ok = False
        else:
            print(f"      SKIP — '{test_word}' not in codebook")

        # Test 2: ESC sentinel is unambiguous
        print("\n  [C2] ESC sentinel test")
        esc_info = unpack_cube96(bytes([0xFF, 0xFF, 0xFF]))
        esc_ok = (esc_info['x'] == 127 and esc_info['y'] == 127 and
                  esc_info['z'] == 127 and
                  esc_info['x'] > MAX_CUBE_COORD and
                  esc_info['y'] > MAX_CUBE_COORD and
                  esc_info['z'] > MAX_CUBE_COORD)
        print(f"      0xFF 0xFF 0xFF → ({esc_info['x']},{esc_info['y']},"
              f"{esc_info['z']}) all > {MAX_CUBE_COORD}: "
              f"{'✓' if esc_ok else '✗'}")
        if not esc_ok:
            cube_ok = False

        # Test 3: MeshLex OOV word roundtrip
        print("\n  [C3] MeshLex OOV roundtrip (inline def)")
        oov_word = "xyzfoo42test"  # guaranteed not in static codebook
        test_text = f"the {oov_word} is active"
        encoded, _ = codec.encode(test_text)
        # Create a fresh decoder to simulate two-node
        codec2 = MuxGridCodec(codebook_size="cube96")
        decoded_text = codec2.decode(encoded, 0)
        oov_ok = decoded_text == test_text.lower()
        print(f"      Encoded '{test_text}' ({len(encoded)} bytes)")
        print(f"      Decoded '{decoded_text}'")
        print(f"      Roundtrip: {'✓' if oov_ok else '✗'}")
        if not oov_ok:
            cube_ok = False

        # Test 4: Two-node simulation (separate encoder + decoder)
        print("\n  [C4] Two-node roundtrip (separate instances)")
        enc_codec = MuxGridCodec(codebook_size="cube96")
        dec_codec = MuxGridCodec(codebook_size="cube96")
        twonode_text = "alert flood warning for the area"
        enc_payload, _ = enc_codec.encode(twonode_text)
        dec_text = dec_codec.decode(enc_payload, 0)
        tn_ok = dec_text == twonode_text.lower()
        print(f"      '{twonode_text}' → {len(enc_payload)} bytes → '{dec_text}'")
        print(f"      Roundtrip: {'✓' if tn_ok else '✗'}")
        if not tn_ok:
            cube_ok = False

        # Test 5: Namespace flag check
        print("\n  [C5] Namespace flag (F0) verification")
        ns_word = "the"
        if ns_word in codec.word_to_xyz:
            x, y, z = codec.word_to_xyz[ns_word]
            packed = pack_cube96(x, y, z, f_namespace=0)
            ns_info = unpack_cube96(packed)
            ns_ok = ns_info['f_namespace'] == 0
            print(f"      Static '{ns_word}': F0={ns_info['f_namespace']}: "
                  f"{'✓' if ns_ok else '✗'}")
            if not ns_ok:
                cube_ok = False
        else:
            print(f"      SKIP — '{ns_word}' not in codebook")

        print(f"\n  {'─' * 74}")
        print(f"  CUBE96 TESTS: {'ALL PASS ✓' if cube_ok else 'FAILURES ✗'}")

    print(f"{'=' * 78}\n")


if __name__ == "__main__":
    main()
