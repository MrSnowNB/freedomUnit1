#!/usr/bin/env python3
"""
paginator.py — Split messages into LoRa-safe chunks for multi-page transmission
=================================================================================
v7.0: Adds paginate_strict() for binary payload chunking with CyberMeshPacket
format. Preserves original text-based paginate() for backward compatibility.

Two modes:
  - paginate():        Text-level chunking with [X/N] headers (legacy v5.0)
  - paginate_strict(): Binary payload chunking into CyberMeshPackets (v7.0)

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import logging
import math
import textwrap

logger = logging.getLogger(__name__)


# ── v5.0 Legacy text paginator (unchanged) ──

def paginate(text: str, max_chars: int = 200) -> list[str]:
    """
    Split text into pages of at most max_chars characters.

    Args:
        text: The message to paginate.
        max_chars: Maximum characters per page (default 200).

    Returns:
        List of page strings. Single messages return a 1-element list.
        Multi-page messages get [1/N] headers prepended.
    """
    text = text.strip()
    if not text:
        return [""]

    # If it fits in one page, return as-is (no header needed)
    if len(text) <= max_chars:
        return [text]

    # Reserve space for page header "[XX/XX] " = max 8 chars
    header_reserve = 8
    usable = max_chars - header_reserve

    # Split at word boundaries using textwrap
    chunks = textwrap.wrap(text, width=usable, break_long_words=True,
                           break_on_hyphens=True)

    if len(chunks) <= 1:
        return chunks if chunks else [text[:max_chars]]

    # Add page headers
    total = len(chunks)
    pages = []
    for i, chunk in enumerate(chunks):
        pages.append(f"[{i+1}/{total}] {chunk}")

    return pages


def reassemble(pages: list[str]) -> str:
    """
    Reassemble pages back into original text by stripping [X/N] headers.

    Args:
        pages: List of page strings, possibly with [X/N] headers.

    Returns:
        Reassembled text with headers stripped and pages joined by space.
    """
    import re
    cleaned = []
    for page in pages:
        # Strip [X/N] header if present
        stripped = re.sub(r'^\[\d+/\d+\]\s*', '', page)
        cleaned.append(stripped)
    return " ".join(cleaned)


# ── v7.0 Binary payload paginator (NEW) ──

def paginate_strict(encoded_bytes: bytes, max_payload: int = 178,
                    codec_id: int = 0x01, priority: int = 0) -> list[bytes]:
    """
    Split encoded binary payload into LoRa-safe packets with CyberMeshPacket
    headers. Each chunk gets a page_num and total_pages in the meta byte.

    Args:
        encoded_bytes: Codec-encoded payload bytes.
        max_payload: Maximum usable payload bytes per packet (after headers).
                     Default 178 for strict mode (180 - 2 header bytes).
        codec_id: Codec ID byte (0x01 Huffman strict, 0x02 MUX strict).
        priority: Priority level 0-3.

    Returns:
        List of complete CyberMeshPacket bytes ready for LoRa TX.
        If payload fits in one packet, returns a 1-element list.
    """
    # Lazy import to avoid circular dependency
    from packet import CyberMeshPacket

    if not encoded_bytes:
        return [CyberMeshPacket.encode(
            codec_id=codec_id,
            payload=b"",
            page_num=0,
            total_pages=1,
            priority=priority,
        )]

    # Calculate number of pages needed
    total = math.ceil(len(encoded_bytes) / max_payload)

    # Cap at 4 pages (meta byte supports 1-4)
    if total > 4:
        logger.warning("paginate_strict: payload needs %d pages but max is 4. "
                       "Truncating.", total)
        total = 4

    chunks = []
    for i in range(total):
        start = i * max_payload
        end = start + max_payload
        chunk_data = encoded_bytes[start:end]

        pkt = CyberMeshPacket.encode(
            codec_id=codec_id,
            payload=chunk_data,
            page_num=i,
            total_pages=total,
            priority=priority,
        )
        chunks.append(pkt)

    logger.info("paginate_strict: %d bytes → %d packets "
                "(max_payload=%d, codec=0x%02X)",
                len(encoded_bytes), len(chunks), max_payload, codec_id)

    return chunks


def reassemble_strict(packets: list[bytes]) -> bytes:
    """
    Reassemble paginated binary packets back into the original payload.

    Args:
        packets: List of CyberMeshPacket bytes, in order.

    Returns:
        Concatenated payload bytes.
    """
    from packet import CyberMeshPacket

    payloads = []
    for pkt_bytes in packets:
        pkt = CyberMeshPacket.decode(pkt_bytes)
        payloads.append(pkt.payload)

    return b"".join(payloads)


# ---------------------------------------------------------------------------
# CLI — standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print("=" * 78)
    print("  PAGINATOR v7.0 — CyberMesh / Liberty Mesh")
    print("=" * 78)

    all_pass = True

    # Test 1: Legacy text paginator (unchanged behavior)
    print("\n  [1] Legacy text paginator — short message")
    pages = paginate("short message")
    ok = len(pages) == 1 and pages[0] == "short message"
    print(f"      Pages: {len(pages)}  Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 2: Legacy text paginator — long message
    print("\n  [2] Legacy text paginator — long message")
    long_msg = ("The flood warning has been issued for Lawrence Township "
                "and all mesh nodes should report their current sensor "
                "readings including water level temperature and battery "
                "status immediately to the central monitoring station "
                "for analysis and emergency response coordination")
    pages = paginate(long_msg, max_chars=200)
    reassembled = reassemble(pages)
    ok = len(pages) > 1 and all(len(p) <= 200 for p in pages)
    print(f"      Pages: {len(pages)}")
    for i, p in enumerate(pages):
        print(f"        [{i+1}] ({len(p)} chars) \"{p[:60]}...\"")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 3: Binary paginator — 500 bytes into 3 packets
    print("\n  [3] Binary paginator — 500 bytes → 3 packets")
    payload = bytes(range(256)) + bytes(range(244))  # 500 bytes
    packets = paginate_strict(payload, max_payload=178, codec_id=0x01)
    reassembled = reassemble_strict(packets)
    ok = (len(packets) == 3 and
          reassembled == payload and
          all(len(p) <= 180 for p in packets))
    print(f"      Input: {len(payload)} bytes")
    print(f"      Packets: {len(packets)}")
    for i, p in enumerate(packets):
        from packet import CyberMeshPacket
        pkt = CyberMeshPacket.decode(p)
        print(f"        [{i}] {len(p)} bytes total, "
              f"payload={len(pkt.payload)} bytes, "
              f"page={pkt.page_num}/{pkt.total_pages}")
    print(f"      Reassembled: {len(reassembled)} bytes")
    print(f"      Lossless: {reassembled == payload}")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 4: Binary paginator — single packet (no pagination needed)
    print("\n  [4] Binary paginator — small payload (no split)")
    small = bytes(range(50))
    packets = paginate_strict(small, max_payload=178, codec_id=0x02)
    ok = len(packets) == 1
    pkt = CyberMeshPacket.decode(packets[0])
    ok = ok and pkt.total_pages == 1 and pkt.page_num == 0
    print(f"      Input: {len(small)} bytes → {len(packets)} packet")
    print(f"      Page: {pkt.page_num}/{pkt.total_pages}")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 5: Edge case — exactly max_payload
    print("\n  [5] Edge case — exactly 178 bytes")
    exact = bytes(range(178))
    packets = paginate_strict(exact, max_payload=178, codec_id=0x01)
    ok = len(packets) == 1
    pkt = CyberMeshPacket.decode(packets[0])
    ok = ok and pkt.payload == exact
    print(f"      Input: {len(exact)} bytes → {len(packets)} packet")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    # Test 6: Edge case — 179 bytes (needs 2 packets)
    print("\n  [6] Edge case — 179 bytes (overflow by 1)")
    over = bytes(range(179))
    packets = paginate_strict(over, max_payload=178, codec_id=0x01)
    reassembled = reassemble_strict(packets)
    ok = len(packets) == 2 and reassembled == over
    print(f"      Input: {len(over)} bytes → {len(packets)} packets")
    print(f"      Lossless: {reassembled == over}")
    print(f"      Result: {'PASS ✓' if ok else 'FAIL ✗'}")
    if not ok: all_pass = False

    print(f"\n{'=' * 78}")
    print(f"  ALL TESTS: {'PASS ✓' if all_pass else 'FAIL ✗'}")
    print(f"{'=' * 78}\n")
