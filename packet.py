#!/usr/bin/env python3
"""
packet.py — CyberMesh v7.1 Packet Format Encode/Decode
========================================================
Binary packet format for LoRa transmission. All modes use a unified
header followed by encoded payload.

Packet format:
  Byte 0: Codec ID
    0x01 = Huffman strict (lossless)
    0x02 = MUX Grid strict (lossless)
    0x03 = Huffman lossy (keyword mode)
    0x04 = MUX Grid lossy (keyword mode)
    0x05 = MUX Cube96 strict (lossless, 3D cube encoding)
    0x06 = MUX Cube96 lossy (keyword mode, 3D cube encoding)

  Byte 1: Meta byte
    Bits 7-5: Page number (0-7, where 0 = single packet)
    Bits 4-3: Total pages (0-3 → 1-4 pages; 0 means single packet)
    Bits 2-1: Priority (0=normal, 1=high, 2=critical, 3=flash)
    Bit  0:   Reserved (0)

  Byte 2 (lossy modes only): Keyword count (N_KW)

  Bytes 2+ (strict) or 3+ (lossy): Payload
    For cube96 strict (0x05), payload is inner format:
      [word_count:1B][def_count:1B][inline_defs...][body...]
    For cube96 lossy (0x06), keyword_count in header byte 2,
      payload is keyword-encoded body.

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Codec ID constants
CODEC_HUFFMAN_STRICT = 0x01
CODEC_MUX_STRICT = 0x02
CODEC_HUFFMAN_LOSSY = 0x03
CODEC_MUX_LOSSY = 0x04
CODEC_MUX_CUBE_STRICT = 0x05
CODEC_MUX_CUBE_LOSSY = 0x06

LOSSY_CODEC_IDS = {CODEC_HUFFMAN_LOSSY, CODEC_MUX_LOSSY, CODEC_MUX_CUBE_LOSSY}
STRICT_CODEC_IDS = {CODEC_HUFFMAN_STRICT, CODEC_MUX_STRICT, CODEC_MUX_CUBE_STRICT}
ALL_CODEC_IDS = LOSSY_CODEC_IDS | STRICT_CODEC_IDS

# Header sizes
STRICT_HEADER_SIZE = 2   # codec_id + meta
LOSSY_HEADER_SIZE = 3    # codec_id + meta + keyword_count

# Max LoRa payload
MAX_LORA_PAYLOAD = 180


@dataclass
class CyberMeshPacket:
    """Decoded CyberMesh packet."""
    codec_id: int           # 0x01-0x04
    page_num: int           # 0-7
    total_pages: int        # 1-4
    priority: int           # 0-3
    keyword_count: int      # 0 for strict modes
    payload: bytes          # encoded data

    @staticmethod
    def encode(codec_id: int, payload: bytes, page_num: int = 0,
               total_pages: int = 1, priority: int = 0,
               keyword_count: int = 0) -> bytes:
        """
        Pack header + payload into bytes.

        Args:
            codec_id: 0x01-0x04
            payload: Encoded data bytes
            page_num: Page number 0-7 (0 = single packet)
            total_pages: Total pages 1-4
            priority: 0=normal, 1=high, 2=critical, 3=flash
            keyword_count: Number of keywords (lossy modes only)

        Returns:
            Complete packet bytes ready for LoRa TX.
        """
        # Validate
        if codec_id not in ALL_CODEC_IDS:
            raise ValueError(f"Invalid codec_id: 0x{codec_id:02X}")
        if not (0 <= page_num <= 7):
            raise ValueError(f"page_num must be 0-7, got {page_num}")
        if not (1 <= total_pages <= 4):
            raise ValueError(f"total_pages must be 1-4, got {total_pages}")
        if not (0 <= priority <= 3):
            raise ValueError(f"priority must be 0-3, got {priority}")

        # Pack meta byte
        meta = (((page_num & 0x07) << 5) |
                (((total_pages - 1) & 0x03) << 3) |
                ((priority & 0x03) << 1))
        # Bit 0 reserved = 0

        header = bytes([codec_id, meta])

        # Lossy modes include keyword count byte
        if codec_id in LOSSY_CODEC_IDS:
            header += bytes([keyword_count & 0xFF])

        pkt = header + payload

        logger.debug("Packet encode: codec=0x%02X page=%d/%d pri=%d "
                     "kw_count=%d payload=%d total=%d bytes",
                     codec_id, page_num, total_pages, priority,
                     keyword_count, len(payload), len(pkt))

        return pkt

    @staticmethod
    def decode(raw: bytes) -> 'CyberMeshPacket':
        """
        Unpack bytes into CyberMeshPacket object.

        Args:
            raw: Raw packet bytes from LoRa RX.

        Returns:
            CyberMeshPacket with all fields populated.
        """
        if len(raw) < 2:
            raise ValueError(f"Packet too short: {len(raw)} bytes (min 2)")

        codec_id = raw[0]
        if codec_id not in ALL_CODEC_IDS:
            raise ValueError(f"Unknown codec_id: 0x{codec_id:02X}")

        # Parse meta byte
        meta = raw[1]
        page_num = (meta >> 5) & 0x07
        total_pages = ((meta >> 3) & 0x03) + 1  # stored as 0-3, means 1-4
        priority = (meta >> 1) & 0x03
        # Bit 0 is reserved

        # Lossy modes have keyword_count at byte 2
        if codec_id in LOSSY_CODEC_IDS:
            if len(raw) < 3:
                raise ValueError(
                    f"Lossy packet too short: {len(raw)} bytes (min 3)")
            keyword_count = raw[2]
            payload = raw[3:]
        else:
            keyword_count = 0
            payload = raw[2:]

        pkt = CyberMeshPacket(
            codec_id=codec_id,
            page_num=page_num,
            total_pages=total_pages,
            priority=priority,
            keyword_count=keyword_count,
            payload=payload,
        )

        logger.debug("Packet decode: codec=0x%02X page=%d/%d pri=%d "
                     "kw_count=%d payload=%d bytes",
                     codec_id, page_num, total_pages, priority,
                     keyword_count, len(payload))

        return pkt

    @property
    def max_payload_bytes(self) -> int:
        """Maximum payload bytes for this packet type."""
        if self.codec_id in LOSSY_CODEC_IDS:
            return MAX_LORA_PAYLOAD - LOSSY_HEADER_SIZE  # 177
        return MAX_LORA_PAYLOAD - STRICT_HEADER_SIZE      # 178

    @property
    def is_lossy(self) -> bool:
        return self.codec_id in LOSSY_CODEC_IDS

    @property
    def is_huffman(self) -> bool:
        return self.codec_id in {CODEC_HUFFMAN_STRICT, CODEC_HUFFMAN_LOSSY}

    @property
    def is_mux(self) -> bool:
        return self.codec_id in {CODEC_MUX_STRICT, CODEC_MUX_LOSSY}

    @property
    def is_cube(self) -> bool:
        return self.codec_id in {CODEC_MUX_CUBE_STRICT, CODEC_MUX_CUBE_LOSSY}

    @property
    def header_size(self) -> int:
        return LOSSY_HEADER_SIZE if self.is_lossy else STRICT_HEADER_SIZE

    def __repr__(self) -> str:
        mode = "lossy" if self.is_lossy else "strict"
        if self.is_cube:
            engine = "cube96"
        elif self.is_huffman:
            engine = "huffman"
        else:
            engine = "mux"
        return (f"CyberMeshPacket(codec=0x{self.codec_id:02X} "
                f"[{engine}/{mode}] page={self.page_num}/{self.total_pages} "
                f"pri={self.priority} kw={self.keyword_count} "
                f"payload={len(self.payload)}B)")


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("=" * 78)
    print("  PACKET FORMAT v7.0 — CyberMesh / Liberty Mesh")
    print("=" * 78)

    all_pass = True

    # Test 1: Strict Huffman packet
    print("\n  [1] Huffman strict — single packet")
    payload = b"\x01\x02\x03\x04\x05"
    pkt_bytes = CyberMeshPacket.encode(
        CODEC_HUFFMAN_STRICT, payload,
        page_num=0, total_pages=1, priority=0)
    decoded = CyberMeshPacket.decode(pkt_bytes)
    ok = (decoded.codec_id == CODEC_HUFFMAN_STRICT and
          decoded.page_num == 0 and
          decoded.total_pages == 1 and
          decoded.priority == 0 and
          decoded.keyword_count == 0 and
          decoded.payload == payload)
    print(f"      Encoded: {len(pkt_bytes)} bytes (header={decoded.header_size})")
    print(f"      {decoded}")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 2: MUX strict — paginated
    print("\n  [2] MUX strict — paginated (page 2/3)")
    payload = b"\xAA\xBB\xCC"
    pkt_bytes = CyberMeshPacket.encode(
        CODEC_MUX_STRICT, payload,
        page_num=1, total_pages=3, priority=2)
    decoded = CyberMeshPacket.decode(pkt_bytes)
    ok = (decoded.codec_id == CODEC_MUX_STRICT and
          decoded.page_num == 1 and
          decoded.total_pages == 3 and
          decoded.priority == 2 and
          decoded.payload == payload)
    print(f"      Encoded: {len(pkt_bytes)} bytes")
    print(f"      {decoded}")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 3: Huffman lossy — keyword mode
    print("\n  [3] Huffman lossy — keyword mode (8 keywords)")
    payload = b"\x10\x20\x30\x40\x50\x60\x70\x80"
    pkt_bytes = CyberMeshPacket.encode(
        CODEC_HUFFMAN_LOSSY, payload,
        keyword_count=8)
    decoded = CyberMeshPacket.decode(pkt_bytes)
    ok = (decoded.codec_id == CODEC_HUFFMAN_LOSSY and
          decoded.keyword_count == 8 and
          decoded.payload == payload and
          decoded.is_lossy and decoded.is_huffman)
    print(f"      Encoded: {len(pkt_bytes)} bytes (header={decoded.header_size})")
    print(f"      {decoded}")
    print(f"      Max payload: {decoded.max_payload_bytes} bytes")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 4: MUX lossy — keyword mode
    print("\n  [4] MUX lossy — keyword mode (5 keywords, high priority)")
    payload = b"\xDE\xAD\xBE\xEF"
    pkt_bytes = CyberMeshPacket.encode(
        CODEC_MUX_LOSSY, payload,
        keyword_count=5, priority=1)
    decoded = CyberMeshPacket.decode(pkt_bytes)
    ok = (decoded.codec_id == CODEC_MUX_LOSSY and
          decoded.keyword_count == 5 and
          decoded.priority == 1 and
          decoded.payload == payload and
          decoded.is_lossy and decoded.is_mux)
    print(f"      Encoded: {len(pkt_bytes)} bytes")
    print(f"      {decoded}")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 5: All 6 codec IDs round-trip
    print("\n  [5] All 6 codec IDs — round-trip")
    for cid, name in [(0x01, "Huffman strict"), (0x02, "MUX strict"),
                       (0x03, "Huffman lossy"), (0x04, "MUX lossy"),
                       (0x05, "Cube96 strict"), (0x06, "Cube96 lossy")]:
        kw = 10 if cid in (0x03, 0x04, 0x06) else 0
        payload = bytes(range(20))
        pkt = CyberMeshPacket.encode(cid, payload, keyword_count=kw)
        dec = CyberMeshPacket.decode(pkt)
        rt_ok = (dec.codec_id == cid and dec.payload == payload and
                 dec.keyword_count == kw)
        print(f"      0x{cid:02X} {name:<16} → "
              f"{'PASS ✓' if rt_ok else 'FAIL ✗'}")
        if not rt_ok: all_pass = False

    # Test 6: Cube96 is_cube property
    print("\n  [6] Cube96 is_cube property")
    pkt_cube = CyberMeshPacket.decode(
        CyberMeshPacket.encode(CODEC_MUX_CUBE_STRICT, b"\x01\x02\x03"))
    cube_ok = pkt_cube.is_cube and not pkt_cube.is_huffman
    print(f"      0x05 is_cube={pkt_cube.is_cube} is_huffman={pkt_cube.is_huffman}: "
          f"{'PASS ✓' if cube_ok else 'FAIL ✗'}")
    if not cube_ok: all_pass = False

    pkt_cube_lossy = CyberMeshPacket.decode(
        CyberMeshPacket.encode(CODEC_MUX_CUBE_LOSSY, b"\x04\x05\x06",
                               keyword_count=5))
    cl_ok = (pkt_cube_lossy.is_cube and pkt_cube_lossy.is_lossy and
             pkt_cube_lossy.keyword_count == 5)
    print(f"      0x06 is_cube={pkt_cube_lossy.is_cube} is_lossy={pkt_cube_lossy.is_lossy} "
          f"kw={pkt_cube_lossy.keyword_count}: "
          f"{'PASS ✓' if cl_ok else 'FAIL ✗'}")
    if not cl_ok: all_pass = False

    print(f"\n  {'─' * 74}")
    print(f"  ALL TESTS: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print(f"{'=' * 78}\n")
