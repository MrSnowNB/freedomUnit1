#!/usr/bin/env python3
"""
bug12_utf8_fix.py — Bug 12 Verification & Fix
===============================================
CyberMesh v7.1 — Mindtech / Liberty Mesh

Demonstrates Huffman's broken Unicode handling and verifies the fix.
Runs entirely on one machine — no radio, no LLM.

Bug 12: _encode_raw() uses `ord(c) & 0x7F` (7-bit ASCII mask) which
silently destroys any codepoint > 127. _decode_raw() reads 7-bit chars,
so even if encoding didn't mask, decoding would truncate.

Fix: Switch from character-level 7-bit to byte-level 8-bit UTF-8.
  - _encode_raw: encode word as UTF-8 bytes, store byte count, 8 bits each
  - _decode_raw: read byte count, read 8-bit bytes, decode UTF-8
  - Length field stays 5 bits (max 31 bytes — enough for any single token)

Drop into freedomUnit1/ root and run:
    python bug12_utf8_fix.py

Author: Mark Snow, Jr. — Mindtech / CyberMesh / Liberty Mesh
Date:   March 2026
"""

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from huffman_codec import MeshHuffmanCodec


# ═══════════════════════════════════════════════════════════════════════════
# TEST VECTORS — tokens that break under 7-bit ASCII encoding
# ═══════════════════════════════════════════════════════════════════════════

# Each entry: (label, test_string, failure_category)
BUG12_VECTORS = [
    # Emoji (multi-byte UTF-8: 3-4 bytes per char)
    ("emoji_siren",       "🚨",                    "emoji"),
    ("emoji_warning",     "⚠️",                    "emoji"),
    ("emoji_check",       "✅",                    "emoji"),
    ("emoji_chart",       "📊",                    "emoji"),
    ("emoji_green",       "🟢",                    "emoji"),

    # Degree symbol (2-byte UTF-8: 0xC2 0xB0)
    ("degree_north",      "40.2171°N",             "unicode_symbol"),
    ("degree_west",       "74.7429°W",             "unicode_symbol"),
    ("degree_temp",       "41°F",                  "unicode_symbol"),

    # Em-dash (3-byte UTF-8: 0xE2 0x80 0x94)
    ("em_dash",           "—",                     "unicode_symbol"),

    # Mixed ASCII + Unicode in one token
    ("gps_coord",         "40.4862°N",             "mixed"),
    ("temp_reading",      "98°F",                  "mixed"),

    # Pure ASCII control (should still work)
    ("ascii_word",        "Trenton",               "ascii_baseline"),
    ("ascii_id",          "KD2ZYX-7",              "ascii_baseline"),
    ("ascii_number",      "08648",                 "ascii_baseline"),
    ("ascii_url",         "ops@libertymesh.net",   "ascii_baseline"),

    # Full sentences from Experiment H that failed roundtrip
    ("sentence_gps",
     "Flood warning active near Trenton NJ 40.2171°N 74.7429°W",
     "sentence"),
    ("sentence_emoji",
     "⚠️ ALERT ⚠️ Sensor grid sectors A3 B7 C12 showing CRITICAL",
     "sentence"),
    ("sentence_mixed",
     "humidity 98% temp 41°F barometric 29.12 inHg",
     "sentence"),
    ("sentence_status",
     "📊 MESHLEX SYNC: 47 dynamic entries across 5 nodes — Trenton ✅",
     "sentence"),
]


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: Reproduce the bug with current codec
# ═══════════════════════════════════════════════════════════════════════════

def run_phase1_reproduce():
    print()
    print("=" * 78)
    print("  PHASE 1: REPRODUCE BUG 12 — Current Huffman _encode_raw / _decode_raw")
    print("=" * 78)
    print("  Method: ord(c) & 0x7F per character — 7-bit ASCII, destroys Unicode")
    print()

    codec = MeshHuffmanCodec(codebook_size="333k")

    results = []
    for label, test_str, category in BUG12_VECTORS:
        try:
            encoded = codec.encode(test_str)
            decoded = codec.decode(encoded)
            ok = (decoded == test_str)
            enc_bytes = len(encoded)
        except Exception as e:
            decoded = f"ERROR: {e}"
            ok = False
            enc_bytes = 0

        results.append({
            "label": label,
            "input": test_str,
            "output": decoded,
            "category": category,
            "ok": ok,
            "enc_bytes": enc_bytes,
        })

        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  [{status}] {label:<20} {category:<16}", end="")
        if ok:
            print(f"  {len(test_str)}B → {enc_bytes}B")
        else:
            # Show what went wrong
            inp_repr = test_str[:30] if len(test_str) <= 30 else test_str[:27] + "..."
            out_repr = decoded[:30] if len(decoded) <= 30 else decoded[:27] + "..."
            print(f"  IN: {inp_repr!r}")
            print(f"  {'':>47}OUT: {out_repr!r}")

    passed = sum(1 for r in results if r["ok"])
    failed = sum(1 for r in results if not r["ok"])
    print(f"\n  {'─' * 74}")
    print(f"  PHASE 1 RESULT: {passed} passed, {failed} failed out of {len(results)}")

    by_cat = {}
    for r in results:
        cat = r["category"]
        if cat not in by_cat:
            by_cat[cat] = {"pass": 0, "fail": 0}
        by_cat[cat]["pass" if r["ok"] else "fail"] += 1

    print(f"\n  By category:")
    for cat, counts in by_cat.items():
        status = "✓ ALL PASS" if counts["fail"] == 0 else f"✗ {counts['fail']} FAIL"
        print(f"    {cat:<20} {status}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: Apply the fix via monkey-patch, re-test
# ═══════════════════════════════════════════════════════════════════════════

def _encode_raw_fixed(word: str) -> str:
    """
    FIXED: Encode OOV word as UTF-8 bytes with 8-bit encoding.

    Old: len(chars) as 5-bit + 7-bit per char  → destroys codepoints > 127
    New: len(utf8_bytes) as 5-bit + 8-bit per byte → preserves all Unicode

    Max 31 bytes (5-bit length field). Any token over 31 UTF-8 bytes
    gets truncated — same limit as before, just measured in bytes not chars.
    """
    raw = word.encode("utf-8")[:31]  # truncate at 31 bytes
    bits = format(len(raw), "05b")
    for byte in raw:
        bits += format(byte, "08b")
    return bits


def _decode_raw_fixed(bits: str, pos: int) -> tuple:
    """
    FIXED: Decode OOV word from UTF-8 bytes with 8-bit decoding.

    Old: read n chars × 7 bits → can't reconstruct multi-byte Unicode
    New: read n bytes × 8 bits → decode as UTF-8 → correct Unicode
    """
    n = int(bits[pos:pos + 5], 2)
    pos += 5
    raw = bytearray()
    for _ in range(n):
        if pos + 8 > len(bits):
            break
        raw.append(int(bits[pos:pos + 8], 2))
        pos += 8
    return raw.decode("utf-8", errors="replace"), pos


def run_phase2_fixed():
    print()
    print("=" * 78)
    print("  PHASE 2: VERIFY FIX — Patched _encode_raw / _decode_raw (UTF-8, 8-bit)")
    print("=" * 78)
    print("  Method: word.encode('utf-8') → 5-bit byte count + 8-bit per byte")
    print()

    codec = MeshHuffmanCodec(codebook_size="333k")

    # Monkey-patch the fix onto the codec
    MeshHuffmanCodec._encode_raw = staticmethod(_encode_raw_fixed)
    MeshHuffmanCodec._decode_raw = staticmethod(_decode_raw_fixed)

    results = []
    for label, test_str, category in BUG12_VECTORS:
        try:
            encoded = codec.encode(test_str)
            decoded = codec.decode(encoded)
            ok = (decoded == test_str)
            enc_bytes = len(encoded)
        except Exception as e:
            decoded = f"ERROR: {e}"
            ok = False
            enc_bytes = 0

        results.append({
            "label": label,
            "input": test_str,
            "output": decoded,
            "category": category,
            "ok": ok,
            "enc_bytes": enc_bytes,
        })

        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"  [{status}] {label:<20} {category:<16}", end="")
        if ok:
            print(f"  {len(test_str.encode('utf-8'))}B → {enc_bytes}B  "
                  f"ratio={len(test_str.encode('utf-8'))/enc_bytes:.2f}:1"
                  if enc_bytes else "")
        else:
            inp_repr = test_str[:30] if len(test_str) <= 30 else test_str[:27] + "..."
            out_repr = decoded[:30] if len(decoded) <= 30 else decoded[:27] + "..."
            print(f"  IN: {inp_repr!r}")
            print(f"  {'':>47}OUT: {out_repr!r}")

    passed = sum(1 for r in results if r["ok"])
    failed = sum(1 for r in results if not r["ok"])
    print(f"\n  {'─' * 74}")
    print(f"  PHASE 2 RESULT: {passed} passed, {failed} failed out of {len(results)}")

    by_cat = {}
    for r in results:
        cat = r["category"]
        if cat not in by_cat:
            by_cat[cat] = {"pass": 0, "fail": 0}
        by_cat[cat]["pass" if r["ok"] else "fail"] += 1

    print(f"\n  By category:")
    for cat, counts in by_cat.items():
        status = "✓ ALL PASS" if counts["fail"] == 0 else f"✗ {counts['fail']} FAIL"
        print(f"    {cat:<20} {status}")

    return results


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: Re-run Experiment H messages with the fix
# ═══════════════════════════════════════════════════════════════════════════

EXPERIMENT_H_MESSAGES = [
    "🚨 Flood warning active near Trenton NJ 40.2171°N 74.7429°W — "
    "Route 1 bridge sensors show 15 feet and rising fast, dispatch EMS now",

    "Liberty-Node-04 reports sensors at Lawrence Township 08648 are offline — "
    "contact dispatch at 609-555-0147 by 1430 hours for backup",

    "Water levels at New Brunswick gauge NB-07 read 12.4 feet at 0800 — "
    "Raritan River overflow expected to hit Highland Park by 1200",

    "⚠️ ALERT ⚠️ Sensor grid sectors A3 B7 C12 showing CRITICAL — "
    "humidity 98% temp 41°F barometric 29.12 inHg #FloodWatch #LibertyMesh",

    "Evacuate Trenton Water Works facility immediately — contamination detected "
    "at pump station PS-14 on Calhoun Street, notify NJDEP and Mercer County OEM",

    "Trenton fire dept responding to Lawrence Township Route 1 bridge — "
    "New Brunswick units staging at Highland Park, Raritan River at 14 feet",

    "Node KD2ZYX-7 at 40.4862°N 74.4518°W reports wind 45 mph gusting 62 — "
    "barometric pressure dropping 28.88 inHg, tornado watch issued",

    "Forward to ops@libertymesh.net — sitrep: 7/10 nodes online, "
    "3 nodes dark since 0600, mesh coverage at 73%, "
    "see https://status.libertymesh.net/live for map",

    "Trenton police confirm Route 1 bridge CLOSED — detour via Route 206 "
    "through Lawrence Township to Princeton, ETA 45 min, "
    "notify New Brunswick and Highland Park staging areas",

    "📊 MESHLEX SYNC: 47 dynamic entries across 5 nodes — Trenton ✅ "
    "Lawrence Township ✅ New Brunswick ✅ Highland Park ✅ "
    "Princeton ✅ Raritan River ✅ Route 1 ✅ codec stable 🟢",
]


def run_phase3_experiment_h():
    print()
    print("=" * 78)
    print("  PHASE 3: RE-RUN EXPERIMENT H MESSAGES — Fixed Huffman vs Original")
    print("=" * 78)
    print()

    # Fixed codec is already patched from Phase 2
    codec = MeshHuffmanCodec(codebook_size="333k")

    total_raw = 0
    total_enc = 0
    rt_ok = 0

    for i, msg in enumerate(EXPERIMENT_H_MESSAGES):
        raw_bytes = len(msg.encode("utf-8"))
        try:
            encoded = codec.encode(msg)
            decoded = codec.decode(encoded)
            enc_bytes = len(encoded)
            ok = (decoded == msg)
        except Exception as e:
            decoded = f"ERROR: {e}"
            enc_bytes = 0
            ok = False

        total_raw += raw_bytes
        total_enc += enc_bytes
        if ok:
            rt_ok += 1

        ratio = raw_bytes / enc_bytes if enc_bytes else 0
        status = "✓" if ok else "✗"
        trunc = msg if len(msg) <= 68 else msg[:65] + "..."
        print(f"  [{status}] Msg {i+1:>2}  {raw_bytes:>3}B → {enc_bytes:>3}B  "
              f"ratio={ratio:.2f}:1")
        print(f"           {trunc}")
        if not ok:
            print(f"           ✗ ROUNDTRIP FAIL")
            dec_trunc = decoded[:72] if len(decoded) <= 72 else decoded[:69] + "..."
            print(f"           GOT: {dec_trunc}")

    agg_ratio = total_raw / total_enc if total_enc else 0
    print(f"\n  {'─' * 74}")
    print(f"  PHASE 3 RESULT: {rt_ok}/10 roundtrip")
    print(f"  Aggregate ratio: {agg_ratio:.3f}:1")
    print(f"  Total: {total_raw}B → {total_enc}B")

    # Compare with Experiment H original (broken) results
    print()
    print(f"  {'─' * 74}")
    print(f"  BEFORE vs AFTER (Huffman 333K Strict)")
    print(f"  {'':>30} {'BEFORE (Bug 12)':>16} {'AFTER (Fixed)':>16}")
    print(f"  {'Roundtrip':<30} {'0/10':>16} {f'{rt_ok}/10':>16}")
    print(f"  {'Aggregate ratio':<30} {'1.391:1':>16} {f'{agg_ratio:.3f}:1':>16}")
    print(f"  {'Total encoded':<30} {'1066B':>16} {f'{total_enc}B':>16}")

    return rt_ok, agg_ratio


# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: Show the exact code diff
# ═══════════════════════════════════════════════════════════════════════════

def print_diff():
    print()
    print("=" * 78)
    print("  PHASE 4: PATCH — Apply to huffman_codec.py")
    print("=" * 78)
    print("""
  Replace these two methods in huffman_codec.py (class MeshHuffmanCodec):

  ─── OLD (BROKEN) ────────────────────────────────────────────────────────

    @staticmethod
    def _encode_raw(word: str) -> str:
        w = word[:31]
        return format(len(w), "05b") + "".join(
            format(ord(c) & 0x7F, "07b") for c in w)

    @staticmethod
    def _decode_raw(bits: str, pos: int) -> tuple[str, int]:
        n = int(bits[pos:pos+5], 2); pos += 5
        chars = []
        for _ in range(n):
            chars.append(chr(int(bits[pos:pos+7], 2))); pos += 7
        return "".join(chars), pos

  ─── NEW (FIXED) ─────────────────────────────────────────────────────────

    @staticmethod
    def _encode_raw(word: str) -> str:
        raw = word.encode("utf-8")[:31]
        bits = format(len(raw), "05b")
        for byte in raw:
            bits += format(byte, "08b")
        return bits

    @staticmethod
    def _decode_raw(bits: str, pos: int) -> tuple[str, int]:
        n = int(bits[pos:pos + 5], 2); pos += 5
        raw = bytearray()
        for _ in range(n):
            if pos + 8 > len(bits):
                break
            raw.append(int(bits[pos:pos + 8], 2)); pos += 8
        return raw.decode("utf-8", errors="replace"), pos

  ─── WHAT CHANGED ────────────────────────────────────────────────────────

    _encode_raw:
      - word[:31]          → word.encode("utf-8")[:31]   (bytes, not chars)
      - len(w) chars       → len(raw) bytes              (byte count)
      - ord(c) & 0x7F, 07b → byte, 08b                   (8-bit, no mask)

    _decode_raw:
      - chr(int(7 bits))   → bytearray + .decode("utf-8") (proper Unicode)
      - 7 bits per char    → 8 bits per byte               (full range)
      - bounds check added → prevents overrun on short data
  """)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 78)
    print("  Bug 12 — Huffman UTF-8 Corruption: Reproduce → Fix → Verify")
    print("  CyberMesh v7.1 — Single-machine codec test (no radio, no LLM)")
    print("=" * 78)

    # Phase 1: Show the bug
    phase1 = run_phase1_reproduce()

    # Phase 2: Patch and re-test individual tokens
    phase2 = run_phase2_fixed()

    # Phase 3: Full Experiment H re-run
    rt_ok, ratio = run_phase3_experiment_h()

    # Phase 4: Show the diff
    print_diff()

    # Final verdict
    print("=" * 78)
    print("  VERDICT")
    print("=" * 78)
    p1_fail = sum(1 for r in phase1 if not r["ok"])
    p2_fail = sum(1 for r in phase2 if not r["ok"])
    print(f"  Phase 1 (reproduce):    {p1_fail} failures confirmed")
    print(f"  Phase 2 (token fix):    {p2_fail} failures remaining")
    print(f"  Phase 3 (full msgs):    {rt_ok}/10 roundtrip, {ratio:.3f}:1 ratio")
    if p2_fail == 0 and rt_ok == 10:
        print(f"\n  ★ Bug 12 FIXED — safe to patch huffman_codec.py")
    elif p2_fail == 0:
        print(f"\n  ◉ Token-level fix works, but {10-rt_ok} sentence(s) still fail")
        print(f"    (likely a separate encoding issue — investigate)")
    else:
        print(f"\n  ✗ Fix incomplete — {p2_fail} token failures remain")
    print("=" * 78)


if __name__ == "__main__":
    main()
